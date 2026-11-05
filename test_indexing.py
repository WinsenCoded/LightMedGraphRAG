"""
Test Indexing & Single Query Verification Script
================================================
Menjalankan pengindeksan dokumen klinis dan 1 kueri uji coba untuk memvalidasi
seluruh pipeline LightMedGraphRAG dari hulu ke hilir.
"""

import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.append(str(Path(__file__).resolve().parent))

from config import DATA_DIR
from light_medgraphrag import LightMedGraphRAGPipeline

def run_integration_test():
    print("[INTEGRATION TEST] Inisialisasi LightMedGraphRAG Pipeline...")
    pipeline = LightMedGraphRAGPipeline()
    
    # 1. Indeks Dokumen
    copd_file = DATA_DIR / "copd_heart_failure_guidelines.txt"
    print(f"\n[STEP 1] Mengindeks berkas: {copd_file.name}...")
    stats = pipeline.index_document(copd_file)
    print(f"Hasil Pengindeksan: {stats}")
    
    assert stats["total_nodes"] > 0, "Gagal membangun simpul graf medis!"
    
    # 2. Uji Coba Kueri
    print("\n[STEP 2] Menjalankan Kueri Klinis Uji Coba...")
    query = (
        "Pasien dengan riwayat PPOK berat dan gagal jantung mengeluh sesak napas. "
        "Diberikan metoprolol dan salbutamol. Apakah kombinasi kedua obat ini aman?"
    )
    res = pipeline.run_query(query)
    print("\n[STEP 3] Validasi Hasil:")
    print(f"  • Latency: {res['latency_seconds']} detik")
    print(f"  • Total Tokens: {res['total_tokens']}")
    print(f"  • Status: {res['status']}")
    assert res["status"] == "SUCCESS", "Generasi klinis gagal!"
    print("\n🎉 INTEGRATION TEST SUKSES BESAR! SELURUH PIPELINE TERVERIFIKASI.")

if __name__ == "__main__":
    run_integration_test()

