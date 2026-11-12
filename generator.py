"""
LightMedGraphRAG - Zero-Loss Context Assembler & Clinical Generator
===================================================================
1. Zero-Loss Context Assembly: Merakit bukti medis terstruktur dari:
   - Node Entitas Medis tervalidasi UMLS / SNOMED CT
   - Bukti Farmakologi tervalidasi RxNorm
   - Peringatan Interaksi Obat Berbahaya (DDI)
   - Narasi Mekanisme Klinis dari Edge Graf
2. Clinical Generator: Menginstruksikan LLM lokal (llama-med) via Ollama
   dengan aturan ketat bebas halusinasi & sitasi kode CUI/RxCUI.
3. Audit Metrics Logger: Mencatat profiler riil (waktu latensi, estimasi token)
   ke storage/logs/audit_metrics.jsonl untuk kebutuhan publikasi ilmiah.
"""

import json
import time
import logging
from typing import Dict, Any, List, Generator
from pathlib import Path
from config import (
    TEMPERATURE_GENERATION,
    MAX_PREDICT_TOKENS, AUDIT_LOG_FILE, AUDIT_LOG_ENABLED
)
from llm_backend import get_llm_provider, BaseLLMProvider

logger = logging.getLogger("ClinicalGenerator")

class ClinicalGenerator:
    """Mesin perakit konteks tanpa distorsi dan generator respons klinis terverifikasi."""
    
    def __init__(self, provider: Any = None):
        if provider is not None:
            self.llm = provider
        else:
            self.llm = get_llm_provider()
        self.model_name = getattr(self.llm, "model_name", "unknown")

    def assemble_zero_loss_context(self, retrieval_result: Dict[str, Any], safety_result: Dict[str, Any]) -> str:
        """Menyusun konteks bukti medis padat tanpa distorsi (Zero-Loss Context)."""
        sections = []

        # 1. Konsep Medis Tervalidasi (UMLS / SNOMED CT)
        matched_nodes = retrieval_result.get("matched_nodes", [])
        expanded_nodes = retrieval_result.get("expanded_nodes", [])
        all_nodes = matched_nodes + expanded_nodes
        
        disease_and_symptoms = []
        drugs = []
        for n in all_nodes:
            d = n.get("data", {})
            std_name = d.get("standard_name") or d.get("raw_mention", "Unknown")
            code = d.get("code", "N/A")
            csystem = d.get("code_system", "UMLS")
            definition = d.get("definition", "")
            
            if csystem == "RxNorm" or d.get("type") == "T4_Medication":
                drugs.append(f"- {std_name} (RxCUI: {code})")
            else:
                entry = f"- {std_name} (Code: {code} [{csystem}])"
                if definition and len(definition) > 10:
                    entry += f"\n  Definisi Baku: {definition[:180]}..."
                disease_and_symptoms.append(entry)

        if disease_and_symptoms:
            sections.append("=== KONSEP & DIAGNOSIS MEDIS TERVALIDASI (UMLS / SNOMED CT) ===")
            sections.extend(disease_and_symptoms[:6])

        if drugs:
            sections.append("\n=== DATA OBAT KLINIS TERVALIDASI (RxNorm - NLM) ===")
            sections.extend(list(set(drugs))[:6])

        # 2. Peringatan Keselamatan Farmakologi (DDI)
        warnings = safety_result.get("warnings", [])
        if warnings:
            sections.append("\n=== ⚠️ PERINGATAN KONTRAINDIKASI & INTERAKSI OBAT BERBAHAYA (RxNorm DDI) ===")
            for w in warnings:
                sections.append(f"- [{w.get('severity', 'WARNING')}]: {w.get('description')}")
        else:
            sections.append("\n=== STATUS KEAMANAN OBAT: Tidak terdeteksi interaksi mayor antar-kombinasi obat yang terindeks ===")

        # 3. Mekanisme Klinis dari Edge Graf Pengetahuan (Lapis G3)
        matched_edges = retrieval_result.get("matched_edges", [])
        if matched_edges:
            sections.append("\n=== MEKANISME PATOFISIOLOGI & HUBUNGAN KAUSAL (Graph Edges) ===")
            for e in matched_edges[:5]:
                edata = e.get("data", {})
                src = edata.get("source", "")
                tgt = edata.get("target", "")
                rel = edata.get("relation", "")
                mech = edata.get("mechanism", "")
                sections.append(f"- {src} [{rel}] {tgt}: {mech}")

        return "\n".join(sections)

    def generate_response(self, patient_query: str, retrieval_result: Dict[str, Any], safety_result: Dict[str, Any]) -> Dict[str, Any]:
        """Menghasilkan respons klinis terstruktur yang wajib mengutip kode bukti CUI/RxCUI."""
        evidence_context = self.assemble_zero_loss_context(retrieval_result, safety_result)
        
        system_prompt = """You are a clinical decision support assistant operating on the LightMedGraphRAG architecture.
Your core principles:
1. Base your answer strictly on the validated medical evidence provided in the context.
2. Explicitly cite UMLS CUI codes and RxNorm RxCUI codes when recommending or assessing diseases and drugs.
3. If there are drug interaction warnings, you MUST highlight them prominently as a primary safety advisory.
4. Structure your response clearly in clinical format:
   - 1. Clinical Assessment (Tinjauan Klinis & Komorbiditas)
   - 2. Therapeutic Recommendation (Rekomendasi Terapi & Alternatif Aman)
   - 3. Safety Warnings (Peringatan Kontraindikasi & Interaksi Obat)
   - 4. Traceable Medical Evidence (Daftar Kode CUI & RxCUI yang Menjadi Dasar Jawaban)
5. Answer in the same language as the query (if Indonesian, answer in professional medical Indonesian)."""

        user_prompt = f"""EVIDENCE CONTEXT:
\"\"\"{evidence_context}\"\"\"

CLINICAL QUERY / KASUS PASIEN:
\"{patient_query}\"

Provide a safe, evidence-grounded, and structured clinical response:"""

        resp = self.llm.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=TEMPERATURE_GENERATION,
            max_tokens=MAX_PREDICT_TOKENS,
            json_mode=False
        )

        result = {
            "query": patient_query,
            "evidence_context": evidence_context,
            "clinical_response": resp.text,
            "latency_seconds": resp.latency_sec,
            "prompt_tokens": resp.prompt_tokens,
            "completion_tokens": resp.completion_tokens,
            "total_tokens": resp.total_tokens,
            "provider": resp.provider,
            "model": resp.model,
            "status": "SUCCESS" if not resp.text.startswith("[Error") else "ERROR"
        }

        # Catat ke log audit persisten untuk pembuktian ilmiah publikasi
        if AUDIT_LOG_ENABLED:
            self._log_audit_metrics(result)

        return result

    def generate_response_stream(
        self,
        patient_query: str,
        retrieval_result: Dict[str, Any],
        safety_result: Dict[str, Any]
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Streaming generator respons klinis secara progresif.
        Memungkinkan Time-to-First-Token (TTFT) < 1 detik di antarmuka web.
        """
        evidence_context = self.assemble_zero_loss_context(retrieval_result, safety_result)
        
        system_prompt = """You are a clinical decision support assistant operating on the LightMedGraphRAG architecture.
Your core principles:
1. Base your answer strictly on the validated medical evidence provided in the context.
2. Explicitly cite UMLS CUI codes and RxNorm RxCUI codes when recommending or assessing diseases and drugs.
3. If there are drug interaction warnings, you MUST highlight them prominently as a primary safety advisory.
4. Structure your response clearly in clinical format:
   - 1. Clinical Assessment (Tinjauan Klinis & Komorbiditas)
   - 2. Therapeutic Recommendation (Rekomendasi Terapi & Alternatif Aman)
   - 3. Safety Warnings (Peringatan Kontraindikasi & Interaksi Obat)
   - 4. Traceable Medical Evidence (Daftar Kode CUI & RxCUI yang Menjadi Dasar Jawaban)
5. Answer in the same language as the query (if Indonesian, answer in professional medical Indonesian)."""

        user_prompt = f"""EVIDENCE CONTEXT:
\"\"\"{evidence_context}\"\"\"

CLINICAL QUERY / KASUS PASIEN:
\"{patient_query}\"

Provide a safe, evidence-grounded, and structured clinical response:"""

        for stream_item in self.llm.generate_stream(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=TEMPERATURE_GENERATION,
            max_tokens=MAX_PREDICT_TOKENS
        ):
            if stream_item.get("done", False):
                final_resp = stream_item.get("response")
                result = {
                    "query": patient_query,
                    "evidence_context": evidence_context,
                    "clinical_response": stream_item.get("accumulated", ""),
                    "latency_seconds": getattr(final_resp, "latency_sec", 0.0),
                    "prompt_tokens": getattr(final_resp, "prompt_tokens", 0),
                    "completion_tokens": getattr(final_resp, "completion_tokens", 0),
                    "total_tokens": getattr(final_resp, "total_tokens", 0),
                    "provider": getattr(final_resp, "provider", "unknown"),
                    "model": getattr(final_resp, "model", self.model_name),
                    "status": "SUCCESS" if not stream_item.get("accumulated", "").startswith("[Error") else "ERROR"
                }
                if AUDIT_LOG_ENABLED:
                    self._log_audit_metrics(result)
                yield {
                    "delta": "",
                    "accumulated": stream_item.get("accumulated", ""),
                    "done": True,
                    "result": result,
                    "evidence_context": evidence_context
                }
            else:
                yield {
                    "delta": stream_item.get("delta", ""),
                    "accumulated": stream_item.get("accumulated", ""),
                    "done": False,
                    "result": None,
                    "evidence_context": evidence_context
                }

    def _log_audit_metrics(self, metric_data: Dict[str, Any]):
        """Menyimpan entri audit log ke berkas .jsonl."""
        try:
            entry = {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "provider": metric_data.get("provider", "unknown"),
                "model": self.model_name,
                "latency_seconds": metric_data["latency_seconds"],
                "prompt_tokens": metric_data["prompt_tokens"],
                "completion_tokens": metric_data["completion_tokens"],
                "total_tokens": metric_data["total_tokens"],
                "status": metric_data["status"],
                "query_preview": metric_data["query"][:80]
            }
            with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"Gagal menulis log audit: {e}")

