---
title: LightMedGraphRAG - Hybrid Clinical Intelligence
emoji: 🏥
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: 5.16.0
app_file: app.py
pinned: false
license: apache-2.0
short_description: Token-Efficient & Safety-Grounded Medical RAG (LightRAG + MedGraphRAG)
---

# 🏥 LightMedGraphRAG: Hybrid Token-Efficient & Safety-Grounded Clinical RAG

> **Pusat Riset Informatika / Riset Biomedis - Badan Riset dan Inovasi Nasional (BRIN)**  
> Implementasi RAG Medis Mutakhir Menggabungkan Arsitektur **LightRAG** (Efisiensi Token & Dual-Level Retrieval) dan **MedGraphRAG** (Grounding Taksonomi UMLS, RxNorm, & Deterministic Safety Gate).

---

## 📌 1. Latar Belakang & Motivasi Ilmiah

Penerapan *Large Language Models* (LLM) di ranah klinis menghadapi dua dilema fundamental:
1. **Risiko Halusinasi & Fatalitas Farmakologis:** Naive RAG berbasis kemiripan teks sering merekomendasikan kombinasi obat berbahaya (seperti beta-bloker non-selektif pada pasien PPOK/Asma) karena hanya mengandalkan kemiripan vektor tanpa verifikasi ontologi medis resmi.
2. **Ledakan Token (*Token Explosion*) & Latensi Tinggi:** Graf pengetahuan konvensional (GraphRAG standar) mengekstrak ribuan subgraf dan menjalankan perangkuman berlapis (*multi-hop community summaries*), menghabiskan puluhan ribu token LLM per kueri dan menimbulkan latensi hingga puluhan detik.

**LightMedGraphRAG** memecahkan kedua masalah ini secara elegan:
- Mengadopsi mekanisme **LightRAG** untuk memangkas konsumsi token hingga **>85%** menggunakan *Dual-Level Retrieval* ($k^{(l)}$ low-level entities & $k^{(g)}$ high-level themes) dan *Key-Value indexing*.
- Mengadopsi mekanisme **MedGraphRAG** untuk menjamin **keamanan klinis absolut** menggunakan pemetaan ontologi resmi NLM NIH (**UMLS Metathesaurus CUI**, **RxNorm RxCUI**), taksonomi entitas $T_1-T_5$, serta gerbang keamanan obat **deterministik (0 token LLM)**.

---

## 🏗️ 2. Arsitektur Sistem

```
                 [ Kueri Pasien / Pertanyaan Klinis ]
                                │
                                ▼
         ┌──────────────────────────────────────────────┐
         │ 1. Ekstraksi Kata Kunci Dual-Level (<100 Tok) │
         │   • kˡ (Low-Level): Obat, Gejala, Organ      │
         │   • kᵍ (High-Level): Tema Patofisiologi      │
         └──────────────────────┬───────────────────────┘
                                │
                                ▼
         ┌──────────────────────────────────────────────┐
         │ 2. Dual-Level Vector Search & Subgraph Exp.  │
         │   • Match kˡ ➔ Simpul Entitas (Nodes)        │
         │   • Match kᵍ ➔ Relasi Patofisiologi (Edges)  │
         │   • 1-Hop Neighborhood Expansion             │
         └──────────────────────┬───────────────────────┘
                                │
                                ▼
         ┌──────────────────────────────────────────────┐
         │ 3. Gerbang Keamanan Farmakologi Deterministik │
         │   • Deteksi RxCUI via NLM RxNorm / FDA Label │
         │   • Pemeriksaan DDI Mayor: BIAYA 0 TOKEN!    │
         └──────────────────────┬───────────────────────┘
                                │
                                ▼
         ┌──────────────────────────────────────────────┐
         │ 4. Zero-Loss Context Assembly & Sintesis     │
         │   • Agregasi bukti tanpa distorsi semantik    │
         │   • Generasi respon terverifikasi CUI/RxCUI   │
         │   • Pencatatan Log Audit Riil (.jsonl)       │
         └──────────────────────────────────────────────┘
```

---

## 📊 3. Analisis Teoretis & Efisiensi Token

Berdasarkan komparasi formal antara Naive RAG, Standar GraphRAG, MedGraphRAG, dan LightMedGraphRAG:

| Komponen Evaluasi | Naive RAG (Vector-Only) | Standard GraphRAG | MedGraphRAG | **LightMedGraphRAG (Ours)** |
| :--- | :--- | :--- | :--- | :--- |
| **Kompleksitas Retrieval** | $\mathcal{O}(N)$ | $\mathcal{O}(|V| + |E| + \text{Comm})$ | $\mathcal{O}(|V_{\text{hop}}|)$ | **$\mathcal{O}(|V_{\text{top}}| + |E_{\text{top}}|)$** |
| **Konsumsi Token / Kueri** | Rendah (~1.500) | Sangat Tinggi (>12.000) | Sedang (~3.500) | **Sangat Hemat (~1.100 - 1.500)** |
| **Grounding Ontologi Medis** | Tidak Ada (Fiktif) | Terbatas (Teks Bebas) | UMLS + SNOMED CT | **NLM UMLS + RxNorm CUI** |
| **Pemeriksaan Interaksi Obat** | Rentan Halusinasi | Rentan Halusinasi | Deterministik | **100% Deterministik (0 Token)** |
| **Pembaruan Inkremental** | Mudah | Sangat Mahal (Re-index) | Mahal | **Inkremental Tanpa Overhead** |

---

## 🚀 4. Deployment ke Hugging Face Spaces

Aplikasi ini dapat langsung dideploy ke **Hugging Face Spaces** secara gratis tanpa membutuhkan infrastruktur GPU lokal:

### Langkah Deploy:
1. Buat **Space baru** di Hugging Face:
   - SDK: **Gradio**
   - Hardware: **CPU Basic (Free)**
2. Hubungkan repositori GitHub ini atau unggah berkas:
   - `app.py`
   - `config.py`
   - `llm_backend.py`
   - `nlm_connectors.py`
   - `medical_indexer.py`
   - `dual_retriever.py`
   - `safety_checker.py`
   - `generator.py`
   - `vector_store.py`
   - `requirements.txt`
   - Folder `storage/` (berisi graf terindeks awal)
3. Di tab **Settings ➔ Variables and secrets** pada Space Anda, tambahkan Secret (opsional):
   - `UMLS_API_KEY`: API Key UMLS Anda dari NLM NIH.
   - `HF_TOKEN`: Hugging Face User Access Token (gratis).
   - `GROQ_API_KEY`: Groq API Key jika ingin inferensi kilat gratis (<1 detik).

---

## 💻 5. Menjalankan di Komputer Lokal (Localhost / Ollama)

```bash
# 1. Clone repositori
git clone https://github.com/WinsenCoded/LightMedGraphRAG.git
cd LightMedGraphRAG

# 2. Buat virtual environment & install dependensi
python -m venv venv
# Aktifkan di Windows:
.\venv\Scripts\activate
# Install paket
pip install -r requirements.txt

# 3. Jalankan aplikasi Web Gradio
python app.py
```
Akses aplikasi melalui browser di `http://127.0.0.1:7860`.

Jika Anda memiliki Ollama lokal, cukup jalankan:
```bash
ollama run llama-med:latest
```
Aplikasi akan secara otomatis mendeteksi server Ollama lokal Anda!

---

## 📝 6. Catatan Integritas Riset & Verifikasi Audit

Untuk memenuhi standar publikasi internasional:
1. **Tidak Ada Metrik Fabrikasi:** Seluruh metrik token, latensi, dan eksekusi dicatat langsung dari pemanggilan API riil ke `storage/logs/audit_metrics.jsonl`.
2. **Kepatuhan API NLM:** Mengacu pada pedoman NLM NIH terkini (termasuk audit penghentian endpoint interaksi RxNav per 2 Januari 2024 dan transisi ke openFDA).
3. **Lisensi Terbuka:** Dirilis di bawah lisensi Apache 2.0 untuk mendukung penelitian terbuka di BRIN.

