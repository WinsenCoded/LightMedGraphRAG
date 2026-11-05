"""
LightMedGraphRAG - NLM Official Connectors
=========================================
Konektor resmi ke U.S. National Library of Medicine (NLM/NIH):
- UMLS Metathesaurus REST API (CUI Lookup, Definisi, Relasi Ontologi, Semantic Types)
- RxNorm REST API (RxCUI Lookup, Approximate Matching, & Drug-Drug Interaction DDI)
Dilengkapi dengan mekanisme persistent caching lokal untuk mencegah pemborosan panggilan API.
"""

import requests
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from config import UMLS_API_KEY, UMLS_BASE_URL, RXNORM_BASE_URL, API_TIMEOUT, CACHE_FILE

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("NLM_Connectors")

class PersistentCache:
    """Cache sederhana berbasis JSON untuk menghemat panggilan API."""
    def __init__(self, cache_file: Path = CACHE_FILE):
        self.cache_file = cache_file
        self.data: Dict[str, Any] = {}
        self.load()

    def load(self):
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception as e:
                logger.warning(f"Gagal memuat cache ({e}), inisialisasi ulang.")
                self.data = {}
        else:
            self.data = {}

    def save(self):
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Gagal menyimpan cache: {e}")

    def get(self, key: str) -> Optional[Any]:
        return self.data.get(key)

    def set(self, key: str, value: Any):
        self.data[key] = value
        self.save()

# Instance cache global
_cache = PersistentCache()


class UMLSConnector:
    """Klien resmi untuk UMLS REST API (Metathesaurus)."""
    
    def __init__(self, api_key: str = UMLS_API_KEY, base_url: str = UMLS_BASE_URL, timeout: int = API_TIMEOUT):
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout

    def search_concept(self, term: str, sabs: Optional[str] = None, page_size: int = 5) -> List[Dict[str, Any]]:
        """Mencari konsep medis dan mengembalikan kandidat CUI, nama baku, dan semantic types.
        
        Args:
            term: Istilah klinis (contoh: 'dyspnea', 'asthma', 'heart failure')
            sabs: Filter sumber kosakata ontologi (contoh: 'SNOMEDCT_US' untuk SNOMED CT)
            page_size: Batas jumlah kandidat teratas
        """
        cache_key = f"umls:search:{term.lower().strip()}:{sabs}:{page_size}"
        cached = _cache.get(cache_key)
        if cached is not None:
            return cached

        url = f"{self.base_url}/search/current"
        params = {
            'apiKey': self.api_key,
            'string': term,
            'pageSize': page_size
        }
        if sabs:
            params['sabs'] = sabs

        try:
            r = requests.get(url, params=params, timeout=self.timeout)
            if r.status_code == 200:
                results = r.json().get('result', {}).get('results', [])
                cleaned = []
                for res in results:
                    cleaned.append({
                        'cui': res.get('ui'),
                        'name': res.get('name'),
                        'rootSource': res.get('rootSource'),
                        'uri': res.get('uri')
                    })
                _cache.set(cache_key, cleaned)
                return cleaned
            else:
                logger.warning(f"UMLS Search HTTP {r.status_code} untuk term '{term}': {r.text[:100]}")
                return []
        except Exception as e:
            logger.error(f"UMLS Connection Error saat mencari '{term}': {e}")
            return []

    def get_definitions(self, cui: str) -> List[Dict[str, str]]:
        """Mengambil definisi klinis resmi dari CUI yang tervalidasi."""
        cache_key = f"umls:def:{cui}"
        cached = _cache.get(cache_key)
        if cached is not None:
            return cached

        url = f"{self.base_url}/content/current/CUI/{cui}/definitions"
        params = {'apiKey': self.api_key}

        try:
            r = requests.get(url, params=params, timeout=self.timeout)
            if r.status_code == 200:
                raw_defs = r.json().get('result', [])
                cleaned_defs = []
                for d in raw_defs[:3]:  # Maksimal 3 definisi teratas
                    cleaned_defs.append({
                        'source': d.get('rootSource', 'UMLS'),
                        'value': d.get('value', '')
                    })
                _cache.set(cache_key, cleaned_defs)
                return cleaned_defs
            return []
        except Exception as e:
            logger.error(f"UMLS Definitions Error untuk CUI {cui}: {e}")
            return []

    def get_relations(self, cui: str, page_size: int = 10) -> List[Dict[str, Any]]:
        """Mengambil relasi ontologis graf (seperti finding_site, causative_agent)."""
        cache_key = f"umls:rel:{cui}:{page_size}"
        cached = _cache.get(cache_key)
        if cached is not None:
            return cached

        url = f"{self.base_url}/content/current/CUI/{cui}/relations"
        params = {'apiKey': self.api_key, 'pageSize': page_size}

        try:
            r = requests.get(url, params=params, timeout=self.timeout)
            if r.status_code == 200:
                raw_rels = r.json().get('result', [])
                cleaned_rels = []
                for rel in raw_rels:
                    cleaned_rels.append({
                        'relationLabel': rel.get('relationLabel'),
                        'additionalRelationLabel': rel.get('additionalRelationLabel'),
                        'relatedId': rel.get('relatedIdName'),
                        'relatedIdUi': rel.get('relatedId')
                    })
                _cache.set(cache_key, cleaned_rels)
                return cleaned_rels
            return []
        except Exception as e:
            logger.error(f"UMLS Relations Error untuk CUI {cui}: {e}")
            return []


class RxNormConnector:
    """Klien resmi untuk RxNorm REST API (National Library of Medicine)."""
    
    def __init__(self, base_url: str = RXNORM_BASE_URL, timeout: int = API_TIMEOUT):
        self.base_url = base_url
        self.timeout = timeout

    def get_rxcui(self, drug_name: str) -> Optional[str]:
        """Mencari kode RxCUI unik berdasarkan nama obat generik atau dagang."""
        cache_key = f"rxnorm:rxcui:{drug_name.lower().strip()}"
        cached = _cache.get(cache_key)
        if cached is not None:
            return cached

        url = f"{self.base_url}/rxcui.json"
        try:
            r = requests.get(url, params={'name': drug_name}, timeout=self.timeout)
            if r.status_code == 200:
                ids = r.json().get('idGroup', {}).get('rxnormId', [])
                res = ids[0] if ids else None
                _cache.set(cache_key, res)
                return res
            return None
        except Exception as e:
            logger.error(f"RxNorm Error saat mencari '{drug_name}': {e}")
            return None

    def approximate_match(self, term: str) -> Optional[Dict[str, Any]]:
        """Mencari obat menggunakan approximate matching jika terjadi variasi ejaan."""
        cache_key = f"rxnorm:approx:{term.lower().strip()}"
        cached = _cache.get(cache_key)
        if cached is not None:
            return cached

        url = f"{self.base_url}/approximateTerm.json"
        try:
            r = requests.get(url, params={'term': term, 'maxEntries': 3}, timeout=self.timeout)
            if r.status_code == 200:
                candidates = r.json().get('approximateGroup', {}).get('candidate', [])
                if candidates:
                    top = candidates[0]
                    res = {
                        'rxcui': top.get('rxcui'),
                        'name': top.get('name'),
                        'score': top.get('score')
                    }
                    _cache.set(cache_key, res)
                    return res
            return None
        except Exception as e:
            logger.error(f"RxNorm Approx Match Error untuk '{term}': {e}")
            return None

    def check_drug_interactions(self, rxcui_list: List[str]) -> List[Dict[str, str]]:
        """Memeriksa interaksi obat berbahaya antar sekumpulan RxCUI secara deterministik.
        
        Endpoint: /REST/interaction/list.json?rxcuis=...
        """
        # Minimal butuh 2 obat untuk mendeteksi interaksi
        valid_rxcuis = sorted(list(set([str(x) for x in rxcui_list if x])))
        if len(valid_rxcuis) < 2:
            return []

        cache_key = f"rxnorm:ddi:{'+'.join(valid_rxcuis)}"
        cached = _cache.get(cache_key)
        if cached is not None:
            return cached

        url = f"{self.base_url}/interaction/list.json"
        try:
            r = requests.get(url, params={'rxcuis': '+'.join(valid_rxcuis)}, timeout=self.timeout)
            if r.status_code == 200:
                pairs = r.json().get('fullInteractionTypeGroup', [])
                interactions = []
                for group in pairs:
                    source_name = group.get('sourceName', 'DrugBank/NLM')
                    for itype in group.get('fullInteractionType', []):
                        comment = itype.get('comment', '')
                        for pair in itype.get('interactionPair', []):
                            desc = pair.get('description', 'No description available')
                            severity = pair.get('severity', 'N/A')
                            interactions.append({
                                'source': source_name,
                                'severity': severity,
                                'description': desc,
                                'comment': comment
                            })
                _cache.set(cache_key, interactions)
                return interactions
            return []
        except Exception as e:
            logger.error(f"RxNorm Interaction Check Error: {e}")
            return []

