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

class SafetyChecker:
    """Mesin penjaga keselamatan farmakologi deterministik."""
    
    def __init__(self):
        self.rxnorm = RxNormConnector()

    def check_safety(self, drug_rxcuis: List[str], additional_drug_names: List[str] = None) -> Dict[str, Any]:
        """Memeriksa interaksi antar RxCUI yang terdeteksi.
        
        Args:
            drug_rxcuis: Daftar RxCUI unik dari subgraf aktif
            additional_drug_names: Nama obat mentah opsional untuk di-resolve
        """
        all_rxcuis = list(set([str(r) for r in drug_rxcuis if r and str(r).isdigit()]))
        
        if additional_drug_names:
            for dname in additional_drug_names:
                rxcui = self.rxnorm.get_rxcui(dname)
                if not rxcui:
                    approx = self.rxnorm.approximate_match(dname)
                    if approx:
                        rxcui = approx.get("rxcui")
                if rxcui and rxcui not in all_rxcuis:
                    all_rxcuis.append(str(rxcui))

        if len(all_rxcuis) < 2:
            return {
                "has_interaction": False,
                "drug_count": len(all_rxcuis),
                "rxcuis": all_rxcuis,
                "warnings": []
            }

        logger.info(f"Memeriksa interaksi obat deterministik untuk {len(all_rxcuis)} RxCUI: {all_rxcuis}...")
        interactions = self.rxnorm.check_drug_interactions(all_rxcuis)
        
        formatted_warnings = []
        for ix in interactions:
            severity = ix.get("severity", "N/A")
            desc = ix.get("description", "")
            source = ix.get("source", "NLM")
            formatted_warnings.append({
                "severity": severity,
                "description": desc,
                "source": source
            })

        return {
            "has_interaction": len(formatted_warnings) > 0,
            "drug_count": len(all_rxcuis),
            "rxcuis": all_rxcuis,
            "warnings": formatted_warnings
        }

