"""
LightMedGraphRAG - Configuration Module
======================================
Konfigurasi terpusat untuk integrasi LightRAG + MedGraphRAG.
Menjaga parameter eksperimen, API credentials, path direktori, dan logger.
"""

import os
from pathlib import Path

# ==============================================================================
# 1. PATH DIREKTORI & PENYIMPANAN DATA
# ==============================================================================
BASE_DIR = Path(__file__).resolve().parent
STORAGE_DIR = BASE_DIR / "storage"
DATA_DIR = BASE_DIR / "data"

GRAPH_STORAGE_DIR = STORAGE_DIR / "graph"
KV_STORAGE_DIR = STORAGE_DIR / "kv"
VECTOR_STORAGE_DIR = STORAGE_DIR / "vectors"
LOG_STORAGE_DIR = STORAGE_DIR / "logs"

# Pastikan seluruh direktori dibuat otomatis
for d in [STORAGE_DIR, DATA_DIR, GRAPH_STORAGE_DIR, KV_STORAGE_DIR, VECTOR_STORAGE_DIR, LOG_STORAGE_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Berkas penyimpanan persisten
GRAPH_FILE = GRAPH_STORAGE_DIR / "medical_knowledge_graph.json"
KV_NODES_FILE = KV_STORAGE_DIR / "kv_nodes.json"
KV_EDGES_FILE = KV_STORAGE_DIR / "kv_edges.json"
CACHE_FILE = STORAGE_DIR / "api_cache.json"
AUDIT_LOG_FILE = LOG_STORAGE_DIR / "audit_metrics.jsonl"

# ==============================================================================
# 2. KONFIGURASI API RESMI (NLM / NIH)
# ==============================================================================
# UMLS Metathesaurus REST API
UMLS_API_KEY = os.getenv("UMLS_API_KEY", "c9de785e-6034-477d-819d-fab0039f7ab1")
UMLS_BASE_URL = "https://uts-ws.nlm.nih.gov/rest"

# RxNorm Drug Data & Interaction REST API
RXNORM_BASE_URL = "https://rxnav.nlm.nih.gov/REST"

# Request Timeout (detik)
API_TIMEOUT = 12
LLM_TIMEOUT = 180  # Timeout khusus untuk generasi LLM lokal (Ollama)

# ==============================================================================
# 3. KONFIGURASI MULTI-BACKEND LLM (LOCAL & CLOUD DEPLOYMENT)
# ==============================================================================
# Mode Provider: 'auto', 'ollama', 'hf', 'groq', 'openai', 'fallback'
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "auto")

# 3A. LOCAL LLM (OLLAMA)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_GENERATE_URL = f"{OLLAMA_BASE_URL}/api/generate"
OLLAMA_EMBED_URL = f"{OLLAMA_BASE_URL}/api/embeddings"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama-med:latest")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "llama3.2:3b")

# 3B. HUGGING FACE INFERENCE API (Untuk Hugging Face Spaces Deployment)
HF_TOKEN = os.getenv("HF_TOKEN", "")
HF_MODEL = os.getenv("HF_MODEL", "meta-llama/Llama-3.1-8B-Instruct")

# 3C. OPENAI / GROQ / OPENROUTER COMPATIBLE CLOUD APIS
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Hyperparameter Generasi Medis (Temperature rendah untuk determinisme faktual)
TEMPERATURE_EXTRACTION = 0.1   # Presisi tinggi untuk ekstraksi entitas & kata kunci
TEMPERATURE_GENERATION = 0.2   # Konsistensi tinggi untuk sintesis klinis
MAX_PREDICT_TOKENS = 1024

# ==============================================================================
# 4. PARAMETER CHUNKING & GRAPH
# ==============================================================================
CHUNK_SIZE = 1200       # Sesuai standar paper LightRAG (1.200 tokens)
CHUNK_OVERLAP = 150     # Overlap untuk menjamin kontinuitas semantik

# Taksonomi Entitas Medis (Berdasarkan taksonomi MedGraphRAG G2)
MEDICAL_ENTITY_TYPES = {
    "T1": "Symptom / Sign",
    "T2": "Disease / Syndrome",
    "T3": "Anatomy / Organ",
    "T4": "Medication / Substance",
    "T5": "Procedure / Test"
}

# ==============================================================================
# 5. PANDUAN REPRODUSIBILITAS RISET (Untuk Publikasi)
# ==============================================================================
RANDOM_SEED = 42
AUDIT_LOG_ENABLED = True

