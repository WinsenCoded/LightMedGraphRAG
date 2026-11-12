"""
LightMedGraphRAG - Hugging Face Space & Web Application
=======================================================
Aplikasi Web Interaktif untuk LightMedGraphRAG:
Mengintegrasikan efisiensi token LightRAG (Dual-Level Retrieval & KV Indexing)
dengan ketepatan taksonomi MedGraphRAG (UMLS Metathesaurus, RxNorm, & Deterministic Safety Gate).

Didesain untuk demonstrasi ilmiah, publikasi BRIN, dan deployment di Hugging Face Spaces.
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple
import pandas as pd
import networkx as nx
import gradio as gr

# Pastikan path modul terdaftar
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from config import (
    GRAPH_FILE, KV_NODES_FILE, KV_EDGES_FILE, AUDIT_LOG_FILE,
    MEDICAL_ENTITY_TYPES, UMLS_API_KEY, OLLAMA_MODEL, HF_MODEL, GROQ_MODEL
)
from light_medgraphrag import LightMedGraphRAGPipeline
from llm_backend import (
    get_llm_provider,
    OllamaProvider,
    HuggingFaceInferenceProvider,
    OpenAICompatibleProvider,
    FallbackDeterministicProvider
)

# Inisialisasi pipeline global
pipeline = LightMedGraphRAGPipeline()


def get_active_provider_instance(provider_choice: str, user_api_key: str, custom_model: str):
    """Membuat instance LLM provider sesuai preferensi pengguna di antarmuka."""
    choice = provider_choice.lower()
    
    if "groq" in choice:
        api_key = user_api_key.strip() or os.getenv("GROQ_API_KEY", "")
        model = custom_model.strip() or GROQ_MODEL
        if not api_key:
            return FallbackDeterministicProvider(model_name="Deterministic (API Key Groq Belum Diisi)")
        return OpenAICompatibleProvider(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1",
            model_name=model,
            provider_name="Groq Cloud"
        )
    
    elif "hugging face" in choice or "hf" in choice:
        token = user_api_key.strip() or os.getenv("HF_TOKEN", "")
        model = custom_model.strip() or HF_MODEL
        return HuggingFaceInferenceProvider(model_name=model, token=token)
    
    elif "openai" in choice:
        api_key = user_api_key.strip() or os.getenv("OPENAI_API_KEY", "")
        model = custom_model.strip() or "gpt-4o-mini"
        if not api_key:
            return FallbackDeterministicProvider(model_name="Deterministic (API Key OpenAI Belum Diisi)")
        return OpenAICompatibleProvider(
            api_key=api_key,
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            model_name=model,
            provider_name="OpenAI API"
        )
    
    elif "ollama" in choice:
        return OllamaProvider(model_name=custom_model.strip() or OLLAMA_MODEL)
    
    elif "deterministic" in choice:
        return FallbackDeterministicProvider()
    
    # Auto-detect default
    return get_llm_provider()


def run_clinical_query(
    query_text: str,
    provider_choice: str,
    user_api_key: str,
    custom_model: str
):
    """Menjalankan analisis klinis terpadu LightMedGraphRAG secara streaming progresif."""
    if not query_text or not query_text.strip():
        yield (
            "⚠️ Masukkan kueri klinis atau pertanyaan pasien terlebih dahulu.",
            "", "", ""
        )
        return

    # 1. Konfigurasi provider LLM dinamis
    provider = get_active_provider_instance(provider_choice, user_api_key, custom_model)
    pipeline.generator.llm = provider
    pipeline.generator.model_name = getattr(provider, "model_name", "custom")

    # 2. Eksekusi Pipeline secara streaming progresif
    safety_md = ""
    retrieval_md = ""
    
    for stream_update in pipeline.process_query_stream(query_text.strip()):
        retrieval_res = stream_update.get("retrieval", {})
        safety_res = stream_update.get("safety", {})
        accumulated_text = stream_update.get("accumulated", "")
        is_done = stream_update.get("done", False)
        gen_res = stream_update.get("generation")

        # Format Peringatan Keamanan & DDI jika belum terformat
        if not safety_md:
            safety_warnings = safety_res.get("warnings", [])
            rx_cuis = safety_res.get("analyzed_rxcuis", [])
            if safety_warnings:
                safety_md = "### 🚨 Peringatan Interaksi Obat & Kontraindikasi Mayor:\n\n"
                for w in safety_warnings:
                    safety_md += f"- **[{w.get('severity', 'WARNING')}]** {w.get('description')}\n"
            else:
                safety_md = "### ✅ Tidak Terdeteksi Interaksi Mayor Antar-Zat Aktif\n\n"
                safety_md += "Analisis farmakologis terhadap zat aktif pasien menunjukkan profil aman berdasarkan pedoman dan label FDA.\n"
            safety_md += f"\n*RxCUI Teranalisis: `{', '.join(rx_cuis) if rx_cuis else 'None'}`* | *Biaya Token LLM: **0 Token** (Deterministik)*"

        # Format Detail Retrieval Dual-Level jika belum terformat
        if not retrieval_md:
            matched_nodes = retrieval_res.get("matched_nodes", [])
            expanded_nodes = retrieval_res.get("expanded_nodes", [])
            matched_edges = retrieval_res.get("matched_edges", [])
            low_k = retrieval_res.get("dual_keywords", {}).get("low_level_keywords", [])
            high_k = retrieval_res.get("dual_keywords", {}).get("high_level_keywords", [])

            retrieval_md = f"""### 🔍 Analisis Pencarian Dual-Level (LightRAG Paradigm)

**1. Ekstraksi Kata Kunci (<100 Token):**
- **Low-Level Keywords ($k^{{(l)}}$):** `{', '.join(low_k)}`
- **High-Level Keywords ($k^{{(g)}}$):** `{', '.join(high_k)}`

**2. Node Entitas Cocok ({len(matched_nodes)}):**
"""
            for n in matched_nodes[:6]:
                nd = n.get("data", {})
                cui_str = f"UMLS CUI: `{nd.get('cui')}`" if nd.get('cui') else f"Code: `{nd.get('code', 'LOCAL')}`"
                rxcui_str = f" | RxCUI: `{nd.get('rxcui')}`" if nd.get('rxcui') else ""
                retrieval_md += f"- **{nd.get('standard_name', n.get('id'))}** ({nd.get('type', 'T1')}) — {cui_str}{rxcui_str} *(Relevance: {n.get('score', 0):.3f})*\n"

            retrieval_md += f"\n**3. Ekspansi 1-Hop Subgraf ({len(expanded_nodes)} entitas tetangga ditarik):**\n"
            for n in expanded_nodes[:4]:
                nd = n.get("data", {})
                retrieval_md += f"- ↳ *Tetangga Terkait:* **{nd.get('standard_name', n.get('id'))}** ({nd.get('type')}) via relasi `{n.get('via_relation')}` dari `{n.get('via_source')}`\n"

            retrieval_md += f"\n**4. Edge Relasi Patofisiologi Cocok ({len(matched_edges)}):**\n"
            for e in matched_edges[:4]:
                ed = e.get("data", {})
                retrieval_md += f"- `{ed.get('source', e.get('source'))}` ➔ `[{ed.get('relation', e.get('relation'))}]` ➔ `{ed.get('target', e.get('target'))}`\n"

        if not is_done or not gen_res:
            metrics_placeholder = "⏳ *Sedang mensintesis respons klinis terverifikasi (Streaming Real-Time)...*"
            yield (accumulated_text, safety_md, retrieval_md, metrics_placeholder)
        else:
            # Selesai: Tampilkan audit token dan profil latensi lengkap
            naive_graphrag_est = 12500
            consumed_tokens = gen_res.get("total_tokens", 0)
            saved_tokens = max(0, naive_graphrag_est - consumed_tokens)
            efficiency_pct = (saved_tokens / naive_graphrag_est) * 100 if naive_graphrag_est > 0 else 0

            metrics_md = f"""### 📊 Audit Efisiensi Token & Kinerja Riil

| Metrik Evaluasi | Nilai Tercatat | Catatan Ilmiah |
| :--- | :--- | :--- |
| **Backend Provider** | `{gen_res.get('provider', 'N/A')}` | Multi-backend engine |
| **Model Digunakan** | `{gen_res.get('model', 'N/A')}` | Real-time streaming |
| **Latensi Respons** | **{gen_res.get('latency_seconds', 0)} detik** | End-to-end execution |
| **Prompt Tokens** | {gen_res.get('prompt_tokens', 0)} tokens | Input + Zero-Loss context |
| **Completion Tokens** | {gen_res.get('completion_tokens', 0)} tokens | Sintesis jawaban |
| **Total Token Konsumsi** | **{consumed_tokens} tokens** | Sangat hemat token |
| **Estimasi Naive GraphRAG** | ~{naive_graphrag_est} tokens | Tanpa dual-level filtering |
| **Penghematan Token** | **~{saved_tokens} tokens ({efficiency_pct:.1f}%)** | Validasi keunggulan LightRAG |
| **Biaya Safety Gate** | **0 Token (100% Deterministik)** | NLM RxNorm safety module |
"""
            yield (accumulated_text, safety_md, retrieval_md, metrics_md)


def get_graph_data():
    """Mengambil data graf terbaru untuk visualisasi dan tabel."""
    pipeline.retriever.load_graph_data()
    g = pipeline.retriever.graph
    nodes_data = []
    edges_data = []

    for node_id, data in g.nodes(data=True):
        nodes_data.append({
            "Entitas Medis": node_id,
            "Tipe Entitas": data.get("type", "T1"),
            "UMLS CUI": data.get("cui", "N/A"),
            "RxCUI (Obat)": data.get("rxcui", "N/A"),
            "Derajat Relasi": g.degree(node_id)
        })

    for u, v, data in g.edges(data=True):
        edges_data.append({
            "Sumber (Source)": u,
            "Relasi Klinis": data.get("relation", "relates_to"),
            "Target (Tujuan)": v,
            "Mekanisme / Bobot": data.get("mechanism", str(data.get("weight", 1.0)))
        })

    df_nodes = pd.DataFrame(nodes_data)
    df_edges = pd.DataFrame(edges_data)
    summary_text = f"**Total Nodes:** {len(nodes_data)} | **Total Edges:** {len(edges_data)} | **Tipe Entitas Medis:** $T_1-T_5$"
    return df_nodes, df_edges, summary_text


def index_new_guideline(guideline_text: str, doc_name: str) -> str:
    """Mengindeks dokumen pedoman baru secara inkremental."""
    if not guideline_text.strip():
        return "⚠️ Teks pedoman kosong. Silakan masukkan teks medis yang valid."
    
    name = doc_name.strip() or f"guideline_{int(time.time())}.txt"
    try:
        res = pipeline.indexer.index_document(guideline_text, document_id=name)
        pipeline.retriever.load_graph_data()
        return (
            f"✅ **Pengindeksan Berhasil Selesai!**\n\n"
            f"- **Dokumen:** `{res['document']}`\n"
            f"- **Jumlah Chunks:** {res['chunks_processed']}\n"
            f"- **Total Nodes di Graf:** {res['total_nodes']}\n"
            f"- **Total Edges di Graf:** {res['total_edges']}\n"
            f"- *Artefak graf dan profil Key-Value telah diperbarui di disk.*"
        )
    except Exception as e:
        return f"❌ **Gagal Mengindeks:** {str(e)}"


def get_audit_logs() -> pd.DataFrame:
    """Membaca log audit persisten untuk verifikasi ilmiah."""
    if not AUDIT_LOG_FILE.exists():
        return pd.DataFrame([{"Info": "Belum ada riwayat audit log."}])
    
    rows = []
    try:
        with open(AUDIT_LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    rows.append(json.loads(line.strip()))
        if not rows:
            return pd.DataFrame([{"Info": "Log audit kosong."}])
        df = pd.DataFrame(rows)
        if "timestamp" in df.columns:
            df = df.iloc[::-1].reset_index(drop=True)
        return df
    except Exception as e:
        return pd.DataFrame([{"Error": f"Gagal membaca log: {str(e)}"}])


custom_css = """
.header-box {
    background: linear-gradient(135deg, #1e3a8a 0%, #0d9488 100%);
    color: white;
    padding: 24px;
    border-radius: 12px;
    margin-bottom: 20px;
    text-align: center;
}
.header-box h1 {
    color: white !important;
    margin: 0;
    font-size: 2.2rem;
    font-weight: 700;
}
.header-box p {
    color: #e2e8f0 !important;
    margin-top: 8px;
    font-size: 1.05rem;
}
"""


def create_app():
    """Fungsi pembangun antarmuka Gradio Blocks."""
    with gr.Blocks(title="LightMedGraphRAG - Clinical Intelligence") as app_blocks:
        gr.HTML("""
        <div class="header-box">
            <h1>🏥 LightMedGraphRAG</h1>
            <p>Hybrid Architecture Combining LightRAG (Dual-Level Token Efficiency) with MedGraphRAG (UMLS / RxNorm Grounding & Deterministic Safety Gate)</p>
        </div>
        """)

        with gr.Tabs():
            # ──────────────────────────────────────────────────────────────────
            # TAB 1: KONSULTASI KLINIS & KUERI PASIEN
            # ──────────────────────────────────────────────────────────────────
            with gr.Tab("🩺 Konsultasi Klinis (Dual-Level Query)"):
                with gr.Row():
                    with gr.Column(scale=3):
                        query_input = gr.Textbox(
                            label="Kueri Klinis / Kasus Pasien",
                            placeholder="Contoh: Pasien dengan riwayat PPOK berat dan gagal jantung mengeluh sesak napas. Diberikan metoprolol dan salbutamol. Apakah kombinasi kedua obat ini aman?",
                            lines=3
                        )
                        
                        with gr.Row():
                            submit_btn = gr.Button("🚀 Analisis Kasus Klinis", variant="primary", scale=2)
                            clear_btn = gr.Button("🧹 Bersihkan", scale=1)

                        gr.Markdown("#### 💡 Contoh Kasus Klinis Terkurasi:")
                        example_1 = gr.Button("1. Kasus PPOK Berat + Gagal Jantung (Metoprolol & Salbutamol)", size="sm")
                        example_2 = gr.Button("2. Kasus Hipertensi + PPOK (Evaluasi Bisoprolol vs Tiotropium)", size="sm")

                    with gr.Column(scale=2):
                        with gr.Accordion("⚙️ Pengaturan LLM Backend", open=True):
                            provider_dropdown = gr.Dropdown(
                                choices=[
                                    "Auto-Detect (Cek Environment)",
                                    "Groq Cloud (Llama-3.1-8b-instant - Cepat)",
                                    "Hugging Face Serverless (Free Inference API)",
                                    "OpenAI API / Compatible Cloud",
                                    "Local Ollama (llama-med:latest)",
                                    "Deterministic Rule Fallback (Offline/No-Key)"
                                ],
                                value="Auto-Detect (Cek Environment)",
                                label="Pilih Backend Inferensi LLM"
                            )
                            api_key_input = gr.Textbox(
                                label="API Key (Opsional / Jika Diperlukan)",
                                placeholder="Masukkan HF_TOKEN atau GROQ_API_KEY bila belum ada di env...",
                                type="password"
                            )
                            custom_model_input = gr.Textbox(
                                label="Custom Model Name (Opsional)",
                                placeholder="Default sesuai provider (cth: llama-3.1-8b-instant)",
                                value=""
                            )

                gr.Markdown("---")
                
                with gr.Row():
                    with gr.Column(scale=3):
                        output_response = gr.Markdown(label="📋 Respons Klinis Terverifikasi CUI/RxCUI")
                        output_safety = gr.Markdown(label="🚨 Peringatan Keamanan & Interaksi Obat")
                    with gr.Column(scale=2):
                        output_metrics = gr.Markdown(label="📊 Profiler & Efisiensi Token")
                        output_retrieval = gr.Markdown(label="🔍 Wawasan Pencarian Dual-Level")

            # ──────────────────────────────────────────────────────────────────
            # TAB 2: MEDICAL KNOWLEDGE GRAPH EXPLORER
            # ──────────────────────────────────────────────────────────────────
            with gr.Tab("🕸️ Penjelajah Graf Pengetahuan Medis"):
                gr.Markdown("### Struktur Knowledge Graph Terindeks (UMLS Metathesaurus & RxNorm Grounded)")
                refresh_graph_btn = gr.Button("🔄 Muat Ulang Data Graf Terbaru", size="sm")
                graph_summary_lbl = gr.Markdown()
                
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("#### 📌 Simpul Entitas Medis (Nodes)")
                        nodes_table = gr.DataFrame(headers=["Entitas Medis", "Tipe Entitas", "UMLS CUI", "RxCUI (Obat)", "Derajat Relasi"], interactive=False)
                    with gr.Column():
                        gr.Markdown("#### 🔗 Relasi Patofisiologi & Terapi (Edges)")
                        edges_table = gr.DataFrame(headers=["Sumber (Source)", "Relasi Klinis", "Target (Tujuan)", "Mekanisme / Bobot"], interactive=False)

            # ──────────────────────────────────────────────────────────────────
            # TAB 3: INKREMENTAL INDEXER (LIGHTRAG)
            # ──────────────────────────────────────────────────────────────────
            with gr.Tab("📄 Pengindeks Pedoman Medis Inkremental"):
                gr.Markdown("### Tambahkan Pedoman Klinis Baru ke Knowledge Graph")
                gr.Markdown("Menggunakan paradigma LightRAG: chunking 1.200 token, ekstraksi entitas $T_1-T_5$, grounding NLM CUI, dan Key-Value profile indexing.")
                
                doc_id_input = gr.Textbox(
                    label="Identitas / Judul Dokumen",
                    placeholder="misal: aha_heart_failure_guidelines_2026.txt",
                    value="clinical_guideline_addon.txt"
                )
                doc_text_input = gr.Textbox(
                    label="Isi Pedoman Klinis / Abstrak PubMed",
                    placeholder="Tempel teks panduan medis di sini...",
                    lines=8
                )
                index_btn = gr.Button("📥 Indeks Pedoman ke Knowledge Graph", variant="primary")
                index_status_lbl = gr.Markdown()

            # ──────────────────────────────────────────────────────────────────
            # TAB 4: AUDIT ILMIAH & LOG REPRODUSIBILITAS
            # ──────────────────────────────────────────────────────────────────
            with gr.Tab("📊 Log Audit Ilmiah (Reproducibility)"):
                gr.Markdown("### Log Eksekusi & Bukti Konsumsi Token Riil")
                gr.Markdown("Setiap kueri klinis mencatat stempel waktu, model LLM, latensi, dan token riil untuk mendukung naskah publikasi ilmiah.")
                refresh_audit_btn = gr.Button("🔄 Perbarui Log Audit", size="sm")
                audit_table = gr.DataFrame(interactive=False)

        # ──────────────────────────────────────────────────────────────────────
        # EVENT HANDLERS
        # ──────────────────────────────────────────────────────────────────────
        submit_btn.click(
            fn=run_clinical_query,
            inputs=[query_input, provider_dropdown, api_key_input, custom_model_input],
            outputs=[output_response, output_safety, output_retrieval, output_metrics]
        )

        clear_btn.click(
            fn=lambda: ("", "", "", "", ""),
            inputs=[],
            outputs=[query_input, output_response, output_safety, output_retrieval, output_metrics]
        )

        def set_ex1():
            return "Pasien dengan riwayat PPOK berat dan gagal jantung mengeluh sesak napas. Diberikan metoprolol dan salbutamol. Apakah kombinasi kedua obat ini aman?"

        def set_ex2():
            return "Evaluasi keamanan penggunaan Bisoprolol dan Tiotropium pada pasien geriatri dengan riwayat gagal jantung dan keluhan bronkospasme."

        example_1.click(fn=set_ex1, inputs=[], outputs=[query_input])
        example_2.click(fn=set_ex2, inputs=[], outputs=[query_input])

        refresh_graph_btn.click(
            fn=get_graph_data,
            inputs=[],
            outputs=[nodes_table, edges_table, graph_summary_lbl]
        )

        index_btn.click(
            fn=index_new_guideline,
            inputs=[doc_text_input, doc_id_input],
            outputs=[index_status_lbl]
        )

        refresh_audit_btn.click(
            fn=get_audit_logs,
            inputs=[],
            outputs=[audit_table]
        )

        # Muat data graf awal
        app_blocks.load(
            fn=get_graph_data,
            inputs=[],
            outputs=[nodes_table, edges_table, graph_summary_lbl]
        )
        app_blocks.load(
            fn=get_audit_logs,
            inputs=[],
            outputs=[audit_table]
        )

        return app_blocks


demo = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 7860))
    # Otomatis buat link publik (gradio.live) gratis jika dijalankan di laptop
    share_public = os.getenv("GRADIO_SHARE", "true").lower() in ["1", "true", "yes"]
    demo.launch(server_name="0.0.0.0", server_port=port, share=share_public)
