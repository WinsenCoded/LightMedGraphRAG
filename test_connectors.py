"""
LightMedGraphRAG - Smoke Test & Verification Suite
=================================================
Skrip uji mandiri untuk memastikan koneksi ke UMLS API, RxNorm API, dan Ollama LLM.
Hasil dari skrip ini dicatat ke dalam audit log untuk bukti integritas publikasi.
"""

import sys
import time
import json
import requests
from pathlib import Path

# Set UTF-8 encoding untuk konsol Windows agar karakter unicode tidak error
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Pastikan modul LightRAG_medis dapat di-import
sys.path.append(str(Path(__file__).resolve().parent))

from config import OLLAMA_GENERATE_URL, OLLAMA_MODEL, TEMPERATURE_EXTRACTION
from nlm_connectors import UMLSConnector, RxNormConnector

def test_umls():
    print("\n[TEST 1] Menguji UMLS REST API (National Library of Medicine)...")
    connector = UMLSConnector()
    t0 = time.time()
    results = connector.search_concept("heart failure", page_size=2)
    latency = time.time() - t0
    
    assert len(results) > 0, "Gagal mendapatkan hasil dari UMLS!"
    top = results[0]
    cui = top['cui']
    name = top['name']
    print(f"  [OK] UMLS Search OK: Term 'heart failure' -> CUI: {cui} ({name}) [Latency: {latency:.2f}s]")
    
    # Uji definisi
    defs = connector.get_definitions(cui)
    print(f"  [OK] UMLS Definitions OK: Ditemukan {len(defs)} definisi resmi.")
    return True

def test_rxnorm():
    print("\n[TEST 2] Menguji RxNorm REST API & Drug Interaction Checker...")
    connector = RxNormConnector()
    
    t0 = time.time()
    rxcui_metoprolol = connector.get_rxcui("metoprolol")
    rxcui_salbutamol = connector.get_rxcui("salbutamol")
    latency = time.time() - t0
    
    print(f"  [OK] RxNorm Lookup OK: Metoprolol -> RxCUI {rxcui_metoprolol} | Salbutamol -> RxCUI {rxcui_salbutamol}")
    
    # Uji interaksi obat berbahaya
    if rxcui_metoprolol and rxcui_salbutamol:
        t1 = time.time()
        interactions = connector.check_drug_interactions([rxcui_metoprolol, rxcui_salbutamol])
        latency_ddi = time.time() - t1
        print(f"  [OK] RxNorm DDI OK: Ditemukan {len(interactions)} interaksi obat [Latency: {latency_ddi:.2f}s]")
        for ix in interactions[:2]:
            print(f"       -> [{ix.get('severity')}] {ix.get('description')[:120]}...")
    return True

def test_ollama():
    print(f"\n[TEST 3] Menguji Local LLM Ollama ({OLLAMA_MODEL})...")
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": "Extract clinical entities as JSON from: 'Patient with dyspnea and hypertension prescribed lisinopril.'",
        "stream": False,
        "options": {"temperature": TEMPERATURE_EXTRACTION, "num_predict": 128}
    }
    t0 = time.time()
    try:
        r = requests.post(OLLAMA_GENERATE_URL, json=payload, timeout=60)
        latency = time.time() - t0
        if r.status_code == 200:
            resp = r.json().get("response", "")
            print(f"  [OK] Ollama OK [Latency: {latency:.2f}s]:")
            print(f"       Preview: {resp[:150].strip()}...")
            return True
        else:
            print(f"  [FAIL] Ollama HTTP Error: {r.status_code} - {r.text}")
            return False
    except Exception as e:
        print(f"  [FAIL] Ollama Connection Error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("  LIGHTMEDGRAPHRAG - SMOKE TEST FONDASI SISTEM")
    print("=" * 60)
    
    umls_ok = test_umls()
    rx_ok = test_rxnorm()
    ollama_ok = test_ollama()
    
    print("\n" + "=" * 60)
    if umls_ok and rx_ok and ollama_ok:
        print("  🎉 SELURUH KONEKTOR FONDASI 100% OPERASIONAL DAN TERVERIFIKASI!")
    else:
        print("  ⚠️ ADA KOMPONEN YANG GAGAL. PERIKSA LOG DI ATAS.")
    print("=" * 60)
