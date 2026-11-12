"""
LightMedGraphRAG - Deterministic Safety & Drug Interaction Checker
==================================================================
Memeriksa interaksi obat berbahaya antar-kandidat obat yang aktif di subgraf
menggunakan database farmakologi U.S. National Library of Medicine (RxNorm API).
Biaya token LLM: 0 Token (Dieksekusi secara deterministik berbasis aturan farmakope).
"""

import logging
from typing import List, Dict, Any
from nlm_connectors import RxNormConnector

logger = logging.getLogger("SafetyChecker")

# Matriks Keamanan Farmakologi Deterministik (Gold Standard FDA / Clinical Guidelines)
DETERMINISTIC_DDI_MATRIX = [
    {
        "drugs": {"6918", "435"},  # Metoprolol (6918) + Albuterol/Salbutamol (435)
        "severity": "HIGH (CONTRAINDICATED)",
        "description": "Beta-bloker (Metoprolol) mengantagonis efek bronkodilatasi Beta-2 agonis (Salbutamol/Albuterol), memicu risiko bronkospasme akut fatal pada pasien PPOK/Asma.",
        "source": "FDA Boxed Warning / GOLD Guidelines"
    },
    {
        "drugs": {"8787", "435"},  # Propranolol (8787) + Albuterol (435)
        "severity": "CRITICAL (CONTRAINDICATED)",
        "description": "Beta-bloker non-selektif (Propranolol) memblokir reseptor Beta-2 di saluran napas, memperberat obstruksi bronkus akut.",
        "source": "FDA Contraindications"
    },
    {
        "drugs": {"20352", "435"},  # Carvedilol (20352) + Albuterol (435)
        "severity": "HIGH (CONTRAINDICATED)",
        "description": "Carvedilol meningkatkan resistensi jalan napas dan menetralkan efek bronkodilator salbutamol.",
        "source": "ACC/AHA Heart Failure Guidelines"
    },
    {
        "drugs": {"25255", "9997"},  # Lisinopril (25255) + Spironolactone (9997)
        "severity": "HIGH (MONITORING REQUIRED)",
        "description": "Kombinasi ACE-inhibitor dan diuretik hemat kalium meningkatkan risiko hiperkalemia berat.",
        "source": "KDIGO Guidelines"
    }
]

# Matriks Kontraindikasi Obat terhadap Komorbiditas Penyakit (Drug-Disease Contraindications - DDC)
DETERMINISTIC_DRUG_DISEASE_MATRIX = [
    {
        "drug_rxcuis": {"20352", "8787", "6918"},  # Carvedilol, Propranolol, Metoprolol
        "disease_terms": ["asma", "asthma", "ppok", "copd", "bronkospasme", "bronchospasm"],
        "severity": "CRITICAL (CONTRAINDICATED)",
        "description": "Beta-bloker dikontraindikasikan pada pasien dengan asma atau bronkospasme aktif karena memblokir reseptor Beta-2 di otot polos bronkus.",
        "source": "FDA Contraindications / GINA Guidelines"
    },
    {
        "drug_rxcuis": {"25255", "3827"},  # Lisinopril, Enalapril
        "disease_terms": ["angioedema", "kehamilan", "pregnancy", "stenosis arteri renalis"],
        "severity": "CRITICAL (CONTRAINDICATED)",
        "description": "ACE Inhibitor dikontraindikasikan mutlak pada riwayat angioedema dan kehamilan (risiko teratogenisitas organogenesis janin).",
        "source": "FDA Boxed Warning"
    }
]

class SafetyChecker:
    """Mesin penjaga keselamatan farmakologi deterministik (DDI & DDC)."""
    
    def __init__(self):
        self.rxnorm = RxNormConnector()

    def check_safety(
        self,
        drug_rxcuis: List[str],
        additional_drug_names: List[str] = None,
        disease_context: List[str] = None
    ) -> Dict[str, Any]:
        """Memeriksa interaksi antar RxCUI dan kontraindikasi penyakit secara deterministik.
        
        Args:
            drug_rxcuis: Daftar RxCUI unik dari subgraf aktif
            additional_drug_names: Nama obat mentah opsional untuk di-resolve
            disease_context: Nama diagnosis/komorbiditas pasien dari subgraf/kueri
        """
        all_rxcuis = list(set([str(r) for r in drug_rxcuis if r and str(r).isdigit()]))
        
        if additional_drug_names:
            for dname in additional_drug_names:
                rxcui = self.rxnorm.get_rxcui(dname)
                if not rxcui:
                    approx = self.rxnorm.approximate_match(dname)
                    if approx:
                        rxcui = approx.get("rxcui")
                if rxcui and str(rxcui) not in all_rxcuis:
                    all_rxcuis.append(str(rxcui))

        formatted_warnings = []
        rx_set = set(all_rxcuis)

        # 1. Periksa Drug-Drug Interactions (DDI) jika terdapat >= 2 obat
        if len(all_rxcuis) >= 2:
            logger.info(f"Memeriksa interaksi obat deterministik untuk {len(all_rxcuis)} RxCUI: {all_rxcuis}...")
            
            # Coba via Online API NLM jika aktif
            interactions = self.rxnorm.check_drug_interactions(all_rxcuis)
            for ix in interactions:
                formatted_warnings.append({
                    "severity": ix.get("severity", "WARNING"),
                    "description": ix.get("description", ""),
                    "source": ix.get("source", "NLM RxNorm")
                })

            # Evaluasi Matriks Offline DDI Deterministik
            for rule in DETERMINISTIC_DDI_MATRIX:
                if rule["drugs"].issubset(rx_set):
                    if not any(rule["severity"] in w.get("severity", "") for w in formatted_warnings):
                        formatted_warnings.append({
                            "severity": rule["severity"],
                            "description": rule["description"],
                            "source": rule["source"]
                        })

        # 2. Periksa Drug-Disease Contraindications (DDC) terhadap konteks penyakit
        if disease_context and all_rxcuis:
            context_text = " ".join([d.lower() for d in disease_context if d])
            for ddc in DETERMINISTIC_DRUG_DISEASE_MATRIX:
                # Periksa apakah ada obat yang cocok
                matching_drugs = ddc["drug_rxcuis"].intersection(rx_set)
                if matching_drugs:
                    # Periksa apakah ada istilah penyakit yang cocok
                    if any(term in context_text for term in ddc["disease_terms"]):
                        if not any(ddc["severity"] in w.get("severity", "") for w in formatted_warnings):
                            formatted_warnings.append({
                                "severity": ddc["severity"],
                                "description": ddc["description"],
                                "source": ddc["source"]
                            })

        return {
            "has_interaction": len(formatted_warnings) > 0,
            "drug_count": len(all_rxcuis),
            "rxcuis": all_rxcuis,
            "warnings": formatted_warnings
        }

