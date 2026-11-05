"""
LightMedGraphRAG - Dual-Level Clinical Retriever
================================================
Mengimplementasikan paradigma Dual-Level Retrieval (LightRAG) untuk ranah medis:
1. Ekstraksi Kata Kunci Dual-Level (<100 Token):
   - Low-Level Keywords (kˡ): Obat spesifik, keluhan/gejala, temuan lab
   - High-Level Keywords (kᵍ): Patofisiologi, sindrom komorbiditas, pedoman terapi
2. Low-Level Vector Search: Mencocokkan kˡ ke Node Entitas Medis.
3. High-Level Vector Search: Mencocokkan kᵍ ke Edge Relasi Patofisiologi.
4. High-Order Neighborhood Expansion: Memperluas subgraf dengan simpul tetangga 1-Hop.
5. Ekstraksi RxCUI Aktif: Mengumpulkan semua kode obat untuk Safety Gate RxNorm.
"""

import json
import logging
import re
import networkx as nx
from typing import List, Dict, Any, Tuple
from pathlib import Path

from config import (
    TEMPERATURE_EXTRACTION,
    GRAPH_FILE, KV_NODES_FILE, KV_EDGES_FILE
)
from vector_store import MedicalDualVectorStore
from llm_backend import get_llm_provider

logger = logging.getLogger("DualRetriever")

class DualLevelClinicalRetriever:
    """Mesin penemu-balik klinis dua tingkat dengan ekspansi subgraf 1-hop."""
    
    def __init__(self):
        self.vector_store = MedicalDualVectorStore()
        self.graph = nx.DiGraph()
        self.kv_nodes: Dict[str, Dict[str, Any]] = {}
        self.kv_edges: Dict[str, Dict[str, Any]] = {}
        self.load_graph_data()

    def load_graph_data(self):
        """Memuat struktur graf, profil Key-Value, dan indeks vektor terbaru."""
        # 1. Muat ulang koleksi vektor dari disk
        self.vector_store.nodes.load()
        self.vector_store.edges.load()

        # 2. Muat ulang graf NetworkX
        if GRAPH_FILE.exists():
            try:
                with open(GRAPH_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.graph = nx.node_link_graph(data, edges="links")
            except Exception as e:
                logger.error(f"Gagal memuat graf untuk retrieval: {e}")

        # 3. Muat profil Key-Value
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

    def extract_dual_keywords(self, clinical_query: str) -> Dict[str, List[str]]:
        """Ekstraksi kata kunci tingkat rendah dan tinggi menggunakan 1 kali panggilan LLM mikro (<100 token)."""
        prompt = f"""Extract dual-level clinical search keywords from this patient query.
1. "low_level_keywords": specific drug names, symptoms, diseases, anatomical locations mentioned directly.
2. "high_level_keywords": broad clinical concepts, disease mechanisms, treatment categories, or safety guidelines.

Clinical Query: "{clinical_query}"

Return ONLY a valid JSON object:
{{
  "low_level_keywords": ["..."],
  "high_level_keywords": ["..."]
}}"""
        try:
            llm = get_llm_provider()
            resp = llm.generate(
                prompt=prompt,
                system_prompt="You are a clinical NLP extractor. Output valid JSON only.",
                temperature=TEMPERATURE_EXTRACTION,
                max_tokens=128,
                json_mode=True
            )
            raw_resp = resp.text.strip()
            if raw_resp.startswith("```"):
                raw_resp = re.sub(r"^```(?:json)?\s*", "", raw_resp)
                raw_resp = re.sub(r"\s*```$", "", raw_resp)
            parsed = json.loads(raw_resp)
            return {
                "low_level_keywords": parsed.get("low_level_keywords", [clinical_query]),
                "high_level_keywords": parsed.get("high_level_keywords", [clinical_query])
            }
        except Exception as e:
            logger.error(f"Gagal mengekstrak kata kunci: {e}")
            return {"low_level_keywords": [clinical_query], "high_level_keywords": [clinical_query]}

    def retrieve(self, query: str, top_k_nodes: int = 5, top_k_edges: int = 5) -> Dict[str, Any]:
        """Menjalankan alur Dual-Level Retrieval lengkap."""
        # 1. Ekstrak Kata Kunci Dual-Level
        keywords = self.extract_dual_keywords(query)
        low_keys = keywords.get("low_level_keywords", [])
        high_keys = keywords.get("high_level_keywords", [])

        logger.info(f"Low-Level Keywords: {low_keys}")
        logger.info(f"High-Level Keywords: {high_keys}")

        # 2. Pencarian Low-Level (Entities / Nodes)
        matched_node_ids = set()
        matched_nodes = []
        for lk in low_keys:
            hits = self.vector_store.nodes.search(lk, top_k=top_k_nodes)
            for doc_id, score, payload in hits:
                if doc_id not in matched_node_ids:
                    matched_node_ids.add(doc_id)
                    matched_nodes.append({"id": doc_id, "score": score, "data": payload})

        # 3. Pencarian High-Level (Relations / Edges)
        matched_edge_ids = set()
        matched_edges = []
        for hk in high_keys:
            hits = self.vector_store.edges.search(hk, top_k=top_k_edges)
            for doc_id, score, payload in hits:
                if doc_id not in matched_edge_ids:
                    matched_edge_ids.add(doc_id)
                    matched_edges.append({"id": doc_id, "score": score, "data": payload})

        # 4. Ekspansi Keterhubungan Tingkat Tinggi (1-Hop Subgraph Neighborhood)
        expanded_node_ids = set()
        expanded_nodes = []
        for n_id in list(matched_node_ids):
            if self.graph.has_node(n_id):
                # Ambil tetangga keluar (successors) dan tetangga masuk (predecessors)
                neighbors = list(self.graph.successors(n_id)) + list(self.graph.predecessors(n_id))
                for neighbor_id in neighbors:
                    if neighbor_id not in matched_node_ids and neighbor_id not in expanded_node_ids:
                        expanded_node_ids.add(neighbor_id)
                        node_payload = self.kv_nodes.get(neighbor_id, {})
                        expanded_nodes.append({"id": neighbor_id, "relation_hop": "1-hop", "data": node_payload})

        # 5. Kumpulkan Seluruh RxCUI Aktif untuk Pemeriksaan Interaksi Obat
        active_rxcuis = []
        all_active_nodes = matched_nodes + expanded_nodes
        for item in all_active_nodes:
            node_data = item.get("data", {})
            if node_data.get("code_system") == "RxNorm" or str(node_data.get("code", "")).isdigit():
                active_rxcuis.append(str(node_data.get("code")))

        # Juga periksa apakah ada obat dari mention teks
        active_rxcuis = list(set([x for x in active_rxcuis if x and x != "N/A"]))

        return {
            "query": query,
            "dual_keywords": keywords,
            "matched_nodes": matched_nodes,
            "matched_edges": matched_edges,
            "expanded_nodes": expanded_nodes,
            "active_rxcuis": active_rxcuis
        }

