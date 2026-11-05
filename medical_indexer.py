"""
LightMedGraphRAG - Medical Knowledge Graph Indexer & Profiler
=============================================================
Menggabungkan paradigma Key-Value Graph Indexing (LightRAG) dengan Taksonomi Medis (MedGraphRAG):
1. Segmentasi Dokumen: Chunk 1200 token.
2. Ekstraksi Entitas & Relasi Klinis: T1 (Gejala), T2 (Penyakit), T3 (Anatomi), T4 (Obat), T5 (Prosedur).
3. Normalisasi Ontologi NLM: Grounding ke UMLS CUI & RxNorm RxCUI.
4. Key-Value Profiling:
   - Node KV: Key = Nama + CUI + Sinonim, Value = Definisi Resmi & Profil Konteks
   - Edge KV: Key = Entitas + Tipe Relasi + Tema Patofisiologi, Value = Narasi Mekanisme Klinis
5. Deduplikasi Graf Deterministik: Menggabungkan simpul identik berbasis CUI unik.
6. Penyimpanan Terpadu: NetworkX Graph + Dual Vector Collections.
"""

import json
import logging
import re
import networkx as nx
from typing import List, Dict, Any, Optional
from pathlib import Path

from config import (
    CHUNK_SIZE, CHUNK_OVERLAP,
    TEMPERATURE_EXTRACTION, GRAPH_FILE, KV_NODES_FILE, KV_EDGES_FILE
)
from nlm_connectors import UMLSConnector, RxNormConnector
from vector_store import MedicalDualVectorStore
from llm_backend import get_llm_provider

logger = logging.getLogger("MedicalIndexer")

class MedicalIndexer:
    """Mesin pengindeks dokumen klinis menjadi Knowledge Graph berbasis Key-Value."""
    
    def __init__(self):
        self.umls = UMLSConnector()
        self.rxnorm = RxNormConnector()
        self.vector_store = MedicalDualVectorStore()
        self.graph = nx.DiGraph()
        self.kv_nodes: Dict[str, Dict[str, Any]] = {}
        self.kv_edges: Dict[str, Dict[str, Any]] = {}
        self.load_existing_graph()

    def load_existing_graph(self):
        """Memuat graf yang sudah ada jika tersedia (untuk pembaruan inkremental)."""
        if GRAPH_FILE.exists():
            try:
                with open(GRAPH_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.graph = nx.node_link_graph(data, edges="links")
                logger.info(f"Graf medis dimuat: {self.graph.number_of_nodes()} node, {self.graph.number_of_edges()} edge.")
            except Exception as e:
                logger.warning(f"Gagal memuat graf lama ({e}), membuat graf baru.")
                self.graph = nx.DiGraph()

        if KV_NODES_FILE.exists():
            try:
                with open(KV_NODES_FILE, "r", encoding="utf-8") as f:
                    self.kv_nodes = json.load(f)
            except Exception:
                self.kv_nodes = {}

        if KV_EDGES_FILE.exists():
            try:
                with open(KV_EDGES_FILE, "r", encoding="utf-8") as f:
                    self.kv_edges = json.load(f)
            except Exception:
                self.kv_edges = {}

    def chunk_text(self, text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
        """Memecah teks mentah menjadi potongan chunk berbasis kata/token."""
        words = text.split()
        chunks = []
        start = 0
        while start < len(words):
            end = start + chunk_size
            chunk_words = words[start:end]
            chunks.append(" ".join(chunk_words))
            start += (chunk_size - overlap)
            if start >= len(words):
                break
        return chunks if chunks else [text]

    def extract_clinical_elements(self, text_chunk: str) -> Dict[str, Any]:
        """Mengekstrak entitas klinis (T1-T5) dan relasi antar-entitas menggunakan LLM lokal dengan format JSON."""
        prompt = f"""Extract clinical entities and direct relationships from the clinical text.
Output JSON only with this structure:
{{
  "entities": {{
    "symptoms": ["list of symptoms/complaints"],
    "diseases": ["list of diseases/syndromes"],
    "anatomy": ["organs/body systems"],
    "drugs": ["medications/substances"],
    "procedures": ["treatments/tests"]
  }},
  "relations": [
    {{"source": "entity A", "target": "entity B", "relation": "contraindicated_with/treats/causes", "mechanism": "brief reason"}}
  ]
}}

Clinical Text:
\"\"\"{text_chunk}\"\"\"

JSON:"""
        try:
            llm = get_llm_provider()
            resp = llm.generate(
                prompt=prompt,
                system_prompt="You are a clinical knowledge graph extractor. Return valid JSON only.",
                temperature=TEMPERATURE_EXTRACTION,
                max_tokens=512,
                json_mode=True
            )
            raw_resp = resp.text.strip()
            if raw_resp.startswith("```"):
                raw_resp = re.sub(r"^```(?:json)?\s*", "", raw_resp)
                raw_resp = re.sub(r"\s*```$", "", raw_resp)
            parsed = json.loads(raw_resp)
            
            # Normalisasi format jika model mengembalikan list entitas
            entities = parsed.get("entities", {})
            if isinstance(entities, list):
                normalized_entities = {"symptoms": [], "diseases": [], "anatomy": [], "drugs": [], "procedures": []}
                for item in entities:
                    if isinstance(item, dict):
                        ename = item.get("name") or item.get("entity", "")
                        etype = (item.get("type") or "symptom").lower()
                        if "drug" in etype or "medicat" in etype:
                            normalized_entities["drugs"].append(ename)
                        elif "disease" in etype or "disorder" in etype:
                            normalized_entities["diseases"].append(ename)
                        elif "symptom" in etype or "sign" in etype:
                            normalized_entities["symptoms"].append(ename)
                        elif "organ" in etype or "anat" in etype:
                            normalized_entities["anatomy"].append(ename)
                        else:
                            normalized_entities["procedures"].append(ename)
                    elif isinstance(item, str):
                        normalized_entities["diseases"].append(item)
                parsed["entities"] = normalized_entities
            return parsed
        except Exception as e:
            logger.error(f"Ekstraksi LLM error: {e}")
            return {"entities": {}, "relations": []}

    def ground_entity_to_nlm(self, entity_name: str, entity_type: str) -> Dict[str, Any]:
        """Menghubungkan entitas klinis ke ontologi resmi UMLS atau RxNorm."""
        entity_name_clean = entity_name.strip()
        
        # Jika tipe obat (T4), utamakan RxNorm
        if entity_type == "drugs":
            rxcui = self.rxnorm.get_rxcui(entity_name_clean)
            if not rxcui:
                approx = self.rxnorm.approximate_match(entity_name_clean)
                if approx:
                    rxcui = approx.get("rxcui")
                    entity_name_clean = approx.get("name", entity_name_clean)
            if rxcui:
                return {
                    "id": f"RXCUI:{rxcui}",
                    "standard_name": entity_name_clean,
                    "type": "T4_Medication",
                    "code_system": "RxNorm",
                    "code": rxcui,
                    "definition": f"RxNorm Standard Medication Concept ({entity_name_clean})"
                }

        # Untuk penyakit, gejala, anatomi, prosedur: cari di UMLS Metathesaurus
        umls_results = self.umls.search_concept(entity_name_clean, page_size=1)
        if umls_results:
            top = umls_results[0]
            cui = top["cui"]
            std_name = top["name"]
            defs = self.umls.get_definitions(cui)
            def_text = defs[0]["value"] if defs else f"Concept: {std_name}"
            return {
                "id": f"CUI:{cui}",
                "standard_name": std_name,
                "type": entity_type,
                "code_system": "UMLS",
                "code": cui,
                "definition": def_text
            }

        # Fallback jika tidak ditemukan di NLM: gunakan nama teks asli
        safe_id = f"LOCAL:{entity_name_clean.lower().replace(' ', '_')}"
        return {
            "id": safe_id,
            "standard_name": entity_name_clean,
            "type": entity_type,
            "code_system": "LOCAL",
            "code": "N/A",
            "definition": f"Clinical entity extracted from text: {entity_name_clean}"
        }

    def index_document(self, doc_text: str, doc_title: str = "Clinical Document") -> Dict[str, Any]:
        """Pipeline utama untuk mengindeks satu dokumen ke dalam Knowledge Graph terpadu."""
        logger.info(f"Memulai pengindeksan dokumen: {doc_title}...")
        chunks = self.chunk_text(doc_text)
        logger.info(f"Dokumen dibagi menjadi {len(chunks)} chunk.")

        total_extracted_entities = 0
        total_extracted_relations = 0

        for chunk_idx, chunk in enumerate(chunks):
            logger.info(f"Memproses Chunk {chunk_idx + 1}/{len(chunks)}...")
            extracted = self.extract_clinical_elements(chunk)
            raw_entities = extracted.get("entities", {})
            raw_relations = extracted.get("relations", [])

            # 1. Proses Entitas & Grounding ke NLM
            grounded_map: Dict[str, Dict[str, Any]] = {}
            for etype, enames in raw_entities.items():
                for name in enames:
                    if not name or len(name.strip()) < 2:
                        continue
                    grounded = self.ground_entity_to_nlm(name, etype)
                    grounded_map[name.lower().strip()] = grounded
                    
                    node_id = grounded["id"]
                    # Key-Value Profiling untuk Node
                    key_phrase = f"{grounded['standard_name']} | {grounded['code']} | {name}"
                    value_profile = {
                        "standard_name": grounded["standard_name"],
                        "code_system": grounded["code_system"],
                        "code": grounded["code"],
                        "type": grounded["type"],
                        "definition": grounded["definition"],
                        "source_doc": doc_title,
                        "raw_mention": name
                    }
                    
                    # Simpan ke graf & KV store (Deduplikasi otomatis oleh node_id)
                    self.graph.add_node(
                        node_id,
                        standard_name=grounded["standard_name"],
                        code=grounded["code"],
                        code_system=grounded["code_system"],
                        entity_type=grounded["type"],
                        definition=grounded["definition"]
                    )
                    self.kv_nodes[node_id] = value_profile
                    self.vector_store.add_node(node_id, key_phrase, value_profile)
                    total_extracted_entities += 1

            # 2. Proses Relasi & Key-Value Profiling untuk Edge
            for rel in raw_relations:
                src_raw = rel.get("source", "").lower().strip()
                tgt_raw = rel.get("target", "").lower().strip()
                rel_type = rel.get("relation", "interacts_with")
                mechanism = rel.get("mechanism", "")

                src_grounded = grounded_map.get(src_raw) or self.ground_entity_to_nlm(src_raw, "general")
                tgt_grounded = grounded_map.get(tgt_raw) or self.ground_entity_to_nlm(tgt_raw, "general")

                u = src_grounded["id"]
                v = tgt_grounded["id"]
                edge_id = f"{u}->{v}::{rel_type}"

                key_edge_phrase = (
                    f"{src_grounded['standard_name']} {rel_type} {tgt_grounded['standard_name']} | "
                    f"{mechanism}"
                )
                value_edge_profile = {
                    "source": src_grounded["standard_name"],
                    "source_id": u,
                    "target": tgt_grounded["standard_name"],
                    "target_id": v,
                    "relation": rel_type,
                    "mechanism": mechanism,
                    "evidence_snippet": chunk[:250] + "..."
                }

                self.graph.add_edge(u, v, relation=rel_type, mechanism=mechanism)
                self.kv_edges[edge_id] = value_edge_profile
                self.vector_store.add_edge(edge_id, key_edge_phrase, value_edge_profile)
                total_extracted_relations += 1

        # Bangun indeks vektor lokal
        self.vector_store.build_indices()
        self.save_all()

        stats = {
            "document": doc_title,
            "chunks_processed": len(chunks),
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "entities_processed": total_extracted_entities,
            "relations_processed": total_extracted_relations
        }
        logger.info(f"Pengindeksan selesai: {stats}")
        return stats

    def save_all(self):
        """Menyimpan seluruh graf, KV, dan vektor ke disk."""
        # 1. Simpan Graf NetworkX
        try:
            graph_data = nx.node_link_data(self.graph, edges="links")
            with open(GRAPH_FILE, "w", encoding="utf-8") as f:
                json.dump(graph_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Gagal menyimpan graf: {e}")

        # 2. Simpan KV Nodes & Edges
        try:
            with open(KV_NODES_FILE, "w", encoding="utf-8") as f:
                json.dump(self.kv_nodes, f, ensure_ascii=False, indent=2)
            with open(KV_EDGES_FILE, "w", encoding="utf-8") as f:
                json.dump(self.kv_edges, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Gagal menyimpan KV data: {e}")

        # 3. Simpan Vektor
        self.vector_store.save_all()
        logger.info("Seluruh artefak Knowledge Graph berhasil disimpan secara persisten.")

