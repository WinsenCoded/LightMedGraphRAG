"""
LightMedGraphRAG - Lightweight Dual-Collection Vector Store
==========================================================
Meniru arsitektur Nano-VectorDB LightRAG dengan implementasi lokal mandiri:
- Mendukung 2 koleksi terpisah:
    1. `nodes_collection`: Menyimpan vektor Key Entitas (CUI, nama, sinonim)
    2. `edges_collection`: Menyimpan vektor Key Relasi (sumber, target, relasi klinis, tema patofisiologi)
- Menggunakan TF-IDF Sublinear N-Gram + Cosine Similarity untuk pencarian deterministik ultra-cepat (<2ms).
- Menyimpan indeks secara persisten di storage/vectors/.
"""

import json
import logging
import numpy as np
from typing import List, Dict, Any, Tuple
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from config import VECTOR_STORAGE_DIR

logger = logging.getLogger("VectorStore")

class LightweightVectorCollection:
    """Koleksi vektor mandiri untuk Node atau Edge."""
    
    def __init__(self, name: str, storage_dir: Path = VECTOR_STORAGE_DIR):
        self.name = name
        self.storage_file = storage_dir / f"vector_collection_{name}.json"
        self.doc_ids: List[str] = []
        self.doc_keys: List[str] = []
        self.doc_payloads: List[Dict[str, Any]] = []
        self.vectorizer: TfidfVectorizer = TfidfVectorizer(
            analyzer="word",
            ngram_range=(1, 2),
            sublinear_tf=True,
            lowercase=True
        )
        self.tfidf_matrix = None
        self.is_fitted = False
        self.load()

    def add_or_update(self, doc_id: str, key_text: str, payload: Dict[str, Any]):
        """Menambahkan atau memperbarui dokumen dalam koleksi vektor."""
        if doc_id in self.doc_ids:
            idx = self.doc_ids.index(doc_id)
            self.doc_keys[idx] = key_text
            self.doc_payloads[idx] = payload
        else:
            self.doc_ids.append(doc_id)
            self.doc_keys.append(key_text)
            self.doc_payloads.append(payload)
        self.is_fitted = False

    def build_index(self):
        """Membangun matriks representasi vektor untuk pencarian."""
        if not self.doc_keys:
            self.tfidf_matrix = None
            self.is_fitted = False
            return
        
        self.tfidf_matrix = self.vectorizer.fit_transform(self.doc_keys)
        self.is_fitted = True

    def search(self, query_text: str, top_k: int = 5) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Mencari dokumen berdasarkan kemiripan kosinus terhadap query.
        
        Returns:
            List of (doc_id, similarity_score, payload)
        """
        if not self.is_fitted or self.tfidf_matrix is None or len(self.doc_ids) == 0:
            self.build_index()
            if not self.is_fitted or self.tfidf_matrix is None:
                return []

        query_vec = self.vectorizer.transform([query_text])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        
        q_clean = query_text.lower().strip()
        # Hybrid boost: jika ada kecocokan leksikal langsung
        for idx, key in enumerate(self.doc_keys):
            if q_clean and (q_clean in key.lower() or any(w in key.lower() for w in q_clean.split() if len(w) > 3)):
                similarities[idx] = max(similarities[idx], 0.35) + 0.25

        # Urutkan berdasarkan skor tertinggi
        ranked_indices = np.argsort(similarities)[::-1]
        results = []
        for idx in ranked_indices[:top_k]:
            score = float(similarities[idx])
            if score > 0.05:  # Threshold relevansi minimal
                results.append((self.doc_ids[idx], score, self.doc_payloads[idx]))
        return results

    def save(self):
        """Menyimpan data koleksi ke berkas JSON lokal."""
        data = {
            "name": self.name,
            "docs": [
                {"id": doc_id, "key": key, "payload": payload}
                for doc_id, key, payload in zip(self.doc_ids, self.doc_keys, self.doc_payloads)
            ]
        }
        try:
            with open(self.storage_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Gagal menyimpan koleksi {self.name}: {e}")

    def load(self):
        """Memuat koleksi dari disk."""
        if self.storage_file.exists():
            try:
                with open(self.storage_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.doc_ids = []
                self.doc_keys = []
                self.doc_payloads = []
                for item in data.get("docs", []):
                    self.doc_ids.append(item["id"])
                    self.doc_keys.append(item["key"])
                    self.doc_payloads.append(item["payload"])
                if self.doc_keys:
                    self.build_index()
            except Exception as e:
                logger.warning(f"Gagal memuat {self.name}: {e}")


class MedicalDualVectorStore:
    """Pengelola terpadu untuk Dual-Collection: Nodes (Entitas) dan Edges (Relasi)."""
    
    def __init__(self, storage_dir: Path = VECTOR_STORAGE_DIR):
        self.nodes = LightweightVectorCollection("nodes", storage_dir)
        self.edges = LightweightVectorCollection("edges", storage_dir)

    def add_node(self, cui_or_id: str, key_phrase: str, node_data: Dict[str, Any]):
        """Menambahkan entitas medis ke koleksi node."""
        self.nodes.add_or_update(cui_or_id, key_phrase, node_data)

    def add_edge(self, edge_id: str, key_phrase: str, edge_data: Dict[str, Any]):
        """Menambahkan relasi medis ke koleksi edge."""
        self.edges.add_or_update(edge_id, key_phrase, edge_data)

    def save_all(self):
        self.nodes.save()
        self.edges.save()

    def build_indices(self):
        self.nodes.build_index()
        self.edges.build_index()

