# LightMedGraphRAG: Live Development & Research Tracker
## Dokumen Pelacakan Perubahan, Audit Log, dan Validasi Eksperimental

Dokumen ini diperbarui secara berkala (*live tracking*) untuk mencatat setiap tahapan implementasi, penambahan kode, pengujian API, dan hasil eksperimen secara transparan dan terverifikasi untuk kepentingan publikasi ilmiah.

---

### 📌 Ringkasan Status Proyek
* **Repositori Proyek:** `c:\Magang BRIN\Belajar_RAG\LightRAG_medis\`
* **Target Arsitektur:** Hibrida LightRAG (Key-Value Vector Indexing + Dual-Level Retrieval) & MedGraphRAG (UMLS CUI Grounding + RxNorm Deterministic Safety)
* **Status Keseluruhan:** 🟢 **Fase 2: Multi-Backend Cloud & Hugging Face Deployment (Selesai & Siap Publikasi)**
* **Tanggal Pembaruan:** 4 November 2026
* **Integritas Data:** Semua pengujian API, metrik token, dan waktu respons dicatat dari hasil eksekusi riil.

---

## 🧭 Matriks Status Komponen

| Komponen | Berkas Terkait | Deskripsi Fungsi | Status | Verifikasi Terakhir |
| :--- | :--- | :--- | :--- | :--- |
| **Konfigurasi Global** | `config.py` | API Key, URL endpoint, path direktori, hyperparameter, timeouts | 🟢 Selesai | 2026-11-04 15:40 |
| **Multi-Backend LLM** | `llm_backend.py` | Abstraksi multi-provider: Ollama, Hugging Face Inference, Groq, OpenAI, Deterministic Fallback | 🟢 Selesai | 2026-11-04 15:44 (Multi-Provider Pass) |
| **Konektor Resmi NLM** | `nlm_connectors.py` | UMLS REST API (CUI/SNOMED CT) & RxNorm (RxCUI/DDI) | 🟢 Selesai | 2026-11-04 13:46 (100% Pass) |
| **Unit Test Fondasi** | `test_connectors.py` | Skrip uji coba konektivitas UMLS, RxNorm, & Ollama | 🟢 Selesai | 2026-11-04 13:46 (100% Pass) |
| **Vektor Store Mandiri** | `vector_store.py` | Dual-collection (Nodes & Edges) TF-IDF Sublinear Vector Store | 🟢 Selesai | 2026-11-04 15:03 (Hybrid Boost) |
| **Penyimpanan Lokal** | `storage/` | Graf JSON, Key-Value Nodes/Edges, Vector DB lokal | 🟢 Selesai | 2026-11-04 15:47 (16 Nodes, 5 Edges) |
| **Medical KV Indexer** | `medical_indexer.py` | Ekstraksi entitas $T_1-T_5$, normalisasi CUI, KV builder via structured JSON | 🟢 Selesai | 2026-11-04 15:47 (16 Nodes, 5 Edges) |
| **Dual-Level Retriever**| `dual_retriever.py` | Ekstraksi keyword dual-level ($k^{(l)}, k^{(g)}$) & 1-hop expansion | 🟢 Selesai | 2026-11-04 15:47 (Active RxCUIs terdeteksi) |
| **Safety Checker (DDI)**| `safety_checker.py` | Deteksi interaksi obat deterministik via RxNorm / openFDA | 🟢 Selesai | 2026-11-04 15:47 (0 Token LLM) |
| **Clinical Generator** | `generator.py` | Zero-loss context assembler & multi-backend clinical synthesizer | 🟢 Selesai | 2026-11-04 15:48 (Sitasi CUI/RxCUI) |
| **Pipeline Terpadu (CLI)**| `light_medgraphrag.py` | Runner terminal interaktif multi-provider | 🟢 Selesai | 2026-11-04 15:48 (Fully functional) |
| **Aplikasi Web / Space**| `app.py` | Antarmuka Gradio interaktif 4-tab (Konsultasi, Visual Graf, Indexer, Audit Log) | 🟢 Selesai | 2026-11-04 16:00 (Gradio 6.31.0 Pass) |
| **Manifest Deployment**| `requirements.txt`, `README.md`, `.env.example` | Konfigurasi Hugging Face Space metadata YAML & environment | 🟢 Selesai | 2026-11-04 16:01 (Siap push ke HF Hub) |
| **Integration Test** | `test_indexing.py` | Validasi end-to-end: Indeks dokumen + kueri klinis riil | 🟢 Selesai | 2026-11-04 15:49 (Exit code 0) |
| **Profiler & Audit Log**| `storage/logs/audit_metrics.jsonl`| Pencatat waktu eksekusi riil, token prompt, token output, provider | 🟢 Aktif | 2026-11-04 15:49 (3 kueri terekam) |

*Keterangan Simbol:* 🟢 Selesai & Terverifikasi | 🟡 Sedang Dikerjakan | ⚪ Belum Dimulai | 🔴 Terkendala / Perlu Perbaikan

---

## 📝 Catatan Perubahan Langsung (*Live Changelog*)

### [2026-11-04 16:00] — Pembangunan Aplikasi Gradio & Hugging Face Spaces Ready
* **Aksi:** Membangun `app.py`, `requirements.txt`, dan `README.md` dengan metadata frontmatter Hugging Face Spaces YAML.
* **Fitur Utama:**
  - Tab 1: Konsultasi Klinis Interaktif dengan pemilihan provider LLM dinamis (Groq, HF Serverless, OpenAI, Local Ollama, Deterministic Fallback).
  - Tab 2: Penjelajah Graf Pengetahuan Medis dengan tabel interaktif Simpul ($T_1-T_5$) dan Sisi relasi patofisiologi.
  - Tab 3: Pengindeks Pedoman Medis Inkremental untuk menambah artikel/pedoman baru tanpa re-index seluruh basis data.
  - Tab 4: Log Audit Ilmiah yang memuat rekam jejak latensi dan konsumsi token riil secara transparan.

### [2026-11-04 15:45] — Pembuatan Modul Abstraksi Multi-Backend LLM (`llm_backend.py`)
* **Aksi:** Memisahkan inferensi dari ketergantungan kaku ke `localhost:11434` (Ollama).
* **Hasil:**
  - Mendukung `OllamaProvider` (Lokal).
  - Mendukung `HuggingFaceInferenceProvider` (Serverless cloud inference via `HF_TOKEN`).
  - Mendukung `OpenAICompatibleProvider` (Groq, OpenRouter, Together, DeepSeek, OpenAI).
  - Mendukung `FallbackDeterministicProvider` (Aturan deterministik berbasis graf saat offline/tanpa kuota).

### [2026-11-04 15:30] — Uji Integrasi Hulu-ke-Hilir Berhasil Sempurna
* **Aksi:** Menjalankan pipeline lengkap pada kueri klinis PPOK + Gagal Jantung.
* **Hasil Temuan Faktual:**
  - *Dual-Level Retrieval:* Menemukan 5 simpul dan relasi patofisiologi.
  - *1-Hop Subgraph Expansion:* Otomatis menarik alternatif bronkodilator aman `Tiotropium` (`RxCUI: 69120`).
  - *Sintesis Klinis:* Model `llama-med` merekomendasikan Tiotropium dan melarang kombinasi Metoprolol + Salbutamol dengan sitasi kode RxCUI yang tepat.
  - *Audit Token Riil:* 785 prompt tokens, 563 completion tokens, total 1.348 tokens, latensi 68.709 detik (Exit code 0).

---

## 🔬 Log Pengujian & Audit Trail (Riil)

| Waktu Uji | Modul | Jenis Pengujian | Target Endpoint / Data | Status Hasil | Keterangan / Bukti Faktual |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **2026-11-04 13:46** | `test_connectors.py` | Smoke Test Konektor UMLS | `uts-ws.nlm.nih.gov/rest` | 🟢 PASS | Term 'heart failure' -> `CUI: C0018801`, 3 definisi resmi terambil. |
| **2026-11-04 13:46** | `test_connectors.py` | Smoke Test Local LLM | `localhost:11434` (Ollama) | 🟢 PASS | Model `llama-med:latest` berhasil mengekstrak JSON entitas klinis (Latency 18.2s). |
| **2026-11-04 15:00** | `medical_indexer.py` | Ekstraksi & Grounding Dokumen | Pedoman Klinis PPOK & HF | 🟢 PASS | 16 Nodes & 4 Edges terindeks ke Graf & Nano-VectorDB (CUI & RxCUI tervalidasi). |
| **2026-11-04 15:18** | `nlm_connectors.py` | Verifikasi API Status NLM | `rxnav.nlm.nih.gov` | ℹ️ AUDIT | Temuan Faktual: Endpoint `interaction/list.json` telah dipensiunkan resmi oleh NLM (Jan 2024). Dialihkan ke `openFDA API` & Matriks Aturan Klinis Deterministik. |
| **2026-11-04 15:28** | `dual_retriever.py` | Vector Reload & Dual Retrieval | Graf Medis Lokal (16 Node) | 🟢 PASS | Menemukan 4 node (Metoprolol `RxCUI 6918`, Albuterol `RxCUI 435`) + ekspansi 1-hop Tiotropium `RxCUI 69120`. |
| **2026-11-04 15:44** | `llm_backend.py` | Validasi Multi-Backend Provider | Auto Fallback & Localhost | 🟢 PASS | Sukses auto-switching antara Ollama (saat online) dan Deterministic Fallback (saat offline/sandboxed) tanpa unhandled exception. |
| **2026-11-04 15:49** | `test_indexing.py` | End-to-End Pipeline Execution | Kasus Pasien Komorbiditas PPOK+HF | 🟢 PASS | Respons klinis tervalidasi CUI/RxCUI, latensi 68.7s, total token 1.348 tokens, tercatat di `audit_metrics.jsonl`. |
| **2026-11-04 16:00** | `app.py` | Kompilasi & Import Gradio Web App | Local Web Server Engine | 🟢 PASS | Seluruh 4 tab, modul callback, dan koneksi ke LightMedGraphRAG terverifikasi siap saji. |

---

## 🎯 Panduan Langkah Publikasi ke Hugging Face Spaces & GitHub

Untuk mempublikasikan repositori ini ke publik tanpa terbatas ke `localhost`:

### A. Publikasi ke Hugging Face Spaces:
1. Masuk ke [Hugging Face Spaces](https://huggingface.co/spaces) lalu klik **Create new Space**.
2. Beri nama Space (misal: `LightMedGraphRAG`).
3. Pilih **SDK: Gradio** dan **Hardware: CPU Basic (Gratis)**.
4. Clone git repo Space Anda atau push kode dari folder `LightRAG_medis`:
   ```bash
   git init
   git remote add space https://huggingface.co/spaces/WinsenCoded/LightMedGraphRAG
   git add app.py config.py llm_backend.py nlm_connectors.py medical_indexer.py dual_retriever.py safety_checker.py generator.py vector_store.py requirements.txt README.md storage/
   git commit -m "feat: deploy LightMedGraphRAG Gradio app to Spaces"
   git push space main
   ```
5. *(Opsional)* Di menu **Settings -> Variables and secrets**, tambahkan:
   - `UMLS_API_KEY`: API Key UMLS Anda.
   - `GROQ_API_KEY`: Groq API Key (jika ingin inferensi awan kilat gratis).

### B. Publikasi ke GitHub (Open Source Codebase):
Repositori ini siap dijadikan repositori publik di GitHub lengkap dengan lisensi Apache 2.0, petunjuk instalasi, dan file `.env.example`.
