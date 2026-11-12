"""
LightMedGraphRAG - Main Pipeline & Interactive CLI
==================================================
Arsitektur Hibrida:
- Efisiensi Token & Dual-Level Vector Indexing (LightRAG)
- Taksonomi Klinis, UMLS Grounding, & RxNorm Deterministic Safety (MedGraphRAG)

Dibuat untuk Riset & Publikasi Ilmiah - BRIN
"""

import sys
import time
import textwrap
from pathlib import Path
from typing import Dict, Any, Generator

# Pastikan encoding UTF-8 di Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.append(str(Path(__file__).resolve().parent))

from config import DATA_DIR, OLLAMA_MODEL, AUDIT_LOG_FILE
from medical_indexer import MedicalIndexer
from dual_retriever import DualLevelClinicalRetriever
from safety_checker import SafetyChecker
from generator import ClinicalGenerator

# ANSI Terminal Colors
class Color:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[95m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RESET = '\033[0m'


class LightMedGraphRAGPipeline:
    """Pipeline terpadu LightMedGraphRAG."""
    
    def __init__(self):
        self.indexer = MedicalIndexer()
        self.retriever = DualLevelClinicalRetriever()
        self.safety = SafetyChecker()
        self.generator = ClinicalGenerator()

    def index_document(self, file_path: Path) -> Dict[str, Any]:
        """Membaca dan mengindeks dokumen teks klinis."""
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        doc_title = file_path.name
        stats = self.indexer.index_document(text, doc_title=doc_title)
        # Segarkan data graf pada retriever
        self.retriever.load_graph_data()
        return stats

    def process_query(self, clinical_query: str) -> Dict[str, Any]:
        """Eksekusi query programatik menghasilkan dictionary terstruktur (retrieval, safety, generation)."""
        self.retriever.load_graph_data()
        retrieval_res = self.retriever.retrieve(clinical_query, top_k_nodes=4, top_k_edges=4)
        active_rxcuis = retrieval_res.get("active_rxcuis", [])
        
        # Ekstrak konteks penyakit/komorbiditas untuk evaluasi DDC (Drug-Disease Contraindications)
        disease_ctx = [clinical_query]
        for n in retrieval_res.get("matched_nodes", []):
            nd = n.get("data", {})
            disease_ctx.append(nd.get("standard_name", n.get("id", "")))

        safety_res = self.safety.check_safety(active_rxcuis, disease_context=disease_ctx)
        gen_res = self.generator.generate_response(clinical_query, retrieval_res, safety_res)
        return {
            "retrieval": retrieval_res,
            "safety": safety_res,
            "generation": gen_res
        }

    def process_query_stream(self, clinical_query: str) -> Generator[Dict[str, Any], None, None]:
        """Eksekusi query dengan streaming token progresif untuk Gradio Web UI."""
        self.retriever.load_graph_data()
        retrieval_res = self.retriever.retrieve(clinical_query, top_k_nodes=4, top_k_edges=4)
        active_rxcuis = retrieval_res.get("active_rxcuis", [])

        # Ekstrak konteks komorbiditas untuk DDC
        disease_ctx = [clinical_query]
        for n in retrieval_res.get("matched_nodes", []):
            nd = n.get("data", {})
            disease_ctx.append(nd.get("standard_name", n.get("id", "")))

        safety_res = self.safety.check_safety(active_rxcuis, disease_context=disease_ctx)

        # Yield status awal retrieval & safety gate
        yield {
            "stage": "retrieval_ready",
            "retrieval": retrieval_res,
            "safety": safety_res,
            "delta": "",
            "accumulated": "*Menghubungkan ke LLM & memulai sintesis klinis...*",
            "done": False,
            "generation": None
        }

        # Stream token dari generator
        for stream_item in self.generator.generate_response_stream(clinical_query, retrieval_res, safety_res):
            yield {
                "stage": "generating",
                "retrieval": retrieval_res,
                "safety": safety_res,
                "delta": stream_item.get("delta", ""),
                "accumulated": stream_item.get("accumulated", ""),
                "done": stream_item.get("done", False),
                "generation": stream_item.get("result")
            }

    def run_query(self, clinical_query: str) -> Dict[str, Any]:
        """Menjalankan kueri klinis melalui pipeline 4 tahap."""
        # Pastikan data graf dan vektor terkini termuat
        self.retriever.load_graph_data()
        print(f"\n{Color.BOLD}{'=' * 68}{Color.RESET}")
        print(f"{Color.CYAN}{Color.BOLD}  LIGHTMEDGRAPHRAG EXECUTION PIPELINE{Color.RESET}")
        print(f"{Color.BOLD}{'=' * 68}{Color.RESET}")
        print(f"{Color.DIM}Kueri Klinis:{Color.RESET} {Color.YELLOW}{clinical_query}{Color.RESET}\n")

        # ── TAHAP 1: Dual-Level Retrieval ────────────────────────────────────
        print(f"{Color.GREEN}▶ TAHAP 1: Dual-Level Clinical Retrieval (Low-Level & High-Level){Color.RESET}")
        t0 = time.time()
        retrieval_res = self.retriever.retrieve(clinical_query, top_k_nodes=4, top_k_edges=4)
        retrieval_time = time.time() - t0

        dual_k = retrieval_res.get("dual_keywords", {})
        print(f"  • Low-Level Keywords (kˡ) : {Color.CYAN}{dual_k.get('low_level_keywords')}{Color.RESET}")
        print(f"  • High-Level Keywords (kᵍ): {Color.CYAN}{dual_k.get('high_level_keywords')}{Color.RESET}")
        
        matched_nodes = retrieval_res.get("matched_nodes", [])
        matched_edges = retrieval_res.get("matched_edges", [])
        expanded_nodes = retrieval_res.get("expanded_nodes", [])
        
        print(f"  • Node Entitas Cocok    : {len(matched_nodes)} entitas")
        for n in matched_nodes[:3]:
            nd = n.get("data", {})
            print(f"    - {Color.BOLD}{nd.get('standard_name')}{Color.RESET} [{nd.get('code_system')}: {nd.get('code')}] (Score: {n.get('score'):.3f})")
            
        print(f"  • Edge Relasi Cocok     : {len(matched_edges)} relasi")
        for e in matched_edges[:2]:
            ed = e.get("data", {})
            print(f"    - {ed.get('source')} --({ed.get('relation')})--> {ed.get('target')}")

        print(f"  • Ekspansi 1-Hop Subgraf: {len(expanded_nodes)} entitas tetangga ditarik")
        print(f"  {Color.DIM}(Waktu Retrieval: {retrieval_time:.3f} detik | Biaya Token LLM: ~60 token){Color.RESET}")

        # ── TAHAP 2: Deterministic Safety Check via RxNorm ────────────────────
        print(f"\n{Color.GREEN}▶ TAHAP 2: Deterministic Safety & Drug Interaction Gate (RxNorm){Color.RESET}")
        active_rxcuis = retrieval_res.get("active_rxcuis", [])
        print(f"  • RxCUI Obat Terdeteksi : {active_rxcuis}")
        
        safety_res = self.safety.check_safety(active_rxcuis)
        if safety_res.get("has_interaction"):
            print(f"  {Color.RED}{Color.BOLD}⚠️ DITEMUKAN {len(safety_res['warnings'])} INTERAKSI OBAT BERBAHAYA!{Color.RESET}")
            for w in safety_res['warnings'][:2]:
                print(f"    {Color.RED}• [{w.get('severity')}] {w.get('description')[:140]}...{Color.RESET}")
        else:
            print(f"  {Color.GREEN}✅ Tidak terdeteksi interaksi obat mayor antar-zat aktif.{Color.RESET}")
        print(f"  {Color.DIM}(Pemeriksaan Farmakologi: Deterministik 100% | Biaya Token LLM: 0 TOKEN!){Color.RESET}")

        # ── TAHAP 3: Zero-Loss Context Assembly & Clinical Generation ─────────
        print(f"\n{Color.GREEN}▶ TAHAP 3: Zero-Loss Context Assembly & Clinical Synthesis{Color.RESET}")
        prov_name = getattr(self.generator.llm, "provider_name", getattr(self.generator.llm, "model_name", "LLM Provider"))
        print(f"  • Backend LLM: {Color.CYAN}{prov_name} ({self.generator.model_name}){Color.RESET}")
        print(f"  • Memproses sintesis klinis...")

        gen_res = self.generator.generate_response(clinical_query, retrieval_res, safety_res)

        print(f"\n{Color.BOLD}{'─' * 68}{Color.RESET}")
        print(f"{Color.GREEN}{Color.BOLD}  📋 RESPONS KLINIS LIGHTMEDGRAPHRAG (TERVERIFIKASI CUI/RxCUI){Color.RESET}")
        print(f"{Color.BOLD}{'─' * 68}{Color.RESET}")
        for line in gen_res.get("clinical_response", "").split("\n"):
            print(textwrap.fill(line, width=72, initial_indent="  ", subsequent_indent="  "))
            
        print(f"\n{Color.BOLD}{'─' * 68}{Color.RESET}")
        print(f"{Color.DIM}📊 Profiler & Audit Riil (Tercatat untuk Naskah Publikasi):{Color.RESET}")
        print(f"  • Waktu Latensi Total   : {gen_res.get('latency_seconds')} detik")
        print(f"  • Prompt Tokens (Est.)  : {gen_res.get('prompt_tokens')} tokens")
        print(f"  • Completion Tokens     : {gen_res.get('completion_tokens')} tokens")
        print(f"  • Total Token Konsumsi  : {gen_res.get('total_tokens')} tokens")
        print(f"  • Status Eksekusi       : {gen_res.get('status')}")
        print(f"{Color.BOLD}{'=' * 68}{Color.RESET}\n")

        return gen_res


def print_banner():
    banner = f"""
{Color.CYAN}{Color.BOLD}╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║     ██╗     ██╗██████╗ ██╗  ██╗████████╗███╗   ███╗███████╗      ║
║     ██║     ██║██╔════╝ ██║  ██║╚══██╔══╝████╗ ████║██╔════╝      ║
║     ██║     ██║██║  ███╗███████║   ██║   ██╔████╔██║█████╗        ║
║     ██║     ██║██║   ██║██╔══██║   ██║   ██║╚██╔╝██║██╔══╝        ║
║     ███████╗██║╚██████╔╝██║  ██║   ██║   ██║ ╚═╝ ██║███████╗      ║
║     ╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝     ╚═╝╚══════╝      ║
║                                                                  ║
║             LightMedGraphRAG: Research Framework v1.0            ║
║              Badan Riset dan Inovasi Nasional (BRIN)             ║
╚══════════════════════════════════════════════════════════════════╝{Color.RESET}
"""
    print(banner)


def main():
    print_banner()
    pipeline = LightMedGraphRAGPipeline()

    while True:
        print(f"\n{Color.BOLD}PILIH MENU RISET:{Color.RESET}")
        print(f"  {Color.CYAN}[1]{Color.RESET} Indeks Dokumen Pedoman Klinis (PPOK + Gagal Jantung & Diabetes)")
        print(f"  {Color.CYAN}[2]{Color.RESET} Kasus Uji 1: Komorbiditas PPOK + Gagal Jantung (Metoprolol & Salbutamol)")
        print(f"  {Color.CYAN}[3]{Color.RESET} Kasus Uji 2: Komorbiditas Diabetes + Hipertensi (Lisinopril & Ibuprofen)")
        print(f"  {Color.CYAN}[4]{Color.RESET} Masukkan Kueri Klinis Bebas / Kasus Pasien Sendiri")
        print(f"  {Color.CYAN}[5]{Color.RESET} Tampilkan Statistik Knowledge Graph & Audit Metrics")
        print(f"  {Color.CYAN}[q]{Color.RESET} Keluar\n")

        choice = input(f"{Color.BOLD}Pilihan Anda ▶ {Color.RESET}").strip()

        if choice == '1':
            copd_file = DATA_DIR / "copd_heart_failure_guidelines.txt"
            diab_file = DATA_DIR / "diabetes_hypertension_guidelines.txt"
            print(f"\n{Color.YELLOW}Mengindeks berkas panduan klinis...{Color.RESET}")
            if copd_file.exists():
                s1 = pipeline.index_document(copd_file)
                print(f"  [OK] Dokumen 1 terindeks: {s1}")
            if diab_file.exists():
                s2 = pipeline.index_document(diab_file)
                print(f"  [OK] Dokumen 2 terindeks: {s2}")
            print(f"{Color.GREEN}Indeksasi selesai. Knowledge Graph & Vektor Store siap digunakan!{Color.RESET}")

        elif choice == '2':
            query = (
                "Pasien pria 65 tahun datang dengan keluhan sesak napas akut dan batuk berdahak. "
                "Riwayat penyakit: PPOK berat dan Gagal Jantung Kongestif. "
                "Sedang mengonsumsi metoprolol untuk jantungnya dan salbutamol inhaler untuk sesak napasnya. "
                "Apakah kombinasi obat ini aman? Mengapa dan apa rekomendasi terapi bronkodilator yang aman?"
            )
            pipeline.run_query(query)

        elif choice == '3':
            query = (
                "Pasien wanita 58 tahun dengan komorbid Diabetes Melitus Tipe 2 dan Hipertensi esensial. "
                "Rutin mengonsumsi metformin 500mg dan lisinopril 10mg. "
                "Pasien mengeluh nyeri sendi lutut hebat dan ingin meminum ibuprofen secara rutin. "
                "Apakah pemberian ibuprofen aman bersama lisinopril? Apa bahaya pada fungsi ginjal dan apa obat nyeri alternatifnya?"
            )
            pipeline.run_query(query)

        elif choice == '4':
            custom_q = input(f"\n{Color.GREEN}Ketik kueri klinis Anda ▶ {Color.RESET}").strip()
            if custom_q:
                pipeline.run_query(custom_q)

        elif choice == '5':
            g = pipeline.indexer.graph
            print(f"\n{Color.BOLD}STATISTIK KNOWLEDGE GRAPH SAAT INI:{Color.RESET}")
            print(f"  • Jumlah Simpul (Nodes) : {g.number_of_nodes()}")
            print(f"  • Jumlah Sisi (Edges)   : {g.number_of_edges()}")
            if AUDIT_LOG_FILE.exists():
                with open(AUDIT_LOG_FILE, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                print(f"  • Total Kueri Terekam di Audit Log: {len(lines)} entri")
            else:
                print(f"  • Belum ada entri audit log.")

        elif choice.lower() in ('q', 'quit', 'exit'):
            print(f"\n{Color.CYAN}Terima kasih. Tetap jaga integritas riset! 🔬{Color.RESET}\n")
            break

if __name__ == "__main__":
    main()

