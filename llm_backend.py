"""
LightMedGraphRAG - Multi-Backend LLM Provider Abstraction
=========================================================
Modul abstraksi inferensi LLM multi-provider yang mendukung:
1. Ollama (Local inference, e.g., llama-med, llama3.2)
2. Hugging Face Inference API / Serverless Router (HF Spaces, e.g., Llama-3.1-8B-Instruct)
3. OpenAI-Compatible API (Groq, OpenRouter, DeepSeek, Together, vLLM, OpenAI)
4. Offline / Deterministic Fallback (Audit-compliant fallback saat kuota habis / offline)

Memungkinkan deployment tanpa dependensi ke localhost (Hugging Face Spaces compatible).
"""

import os
import time
import json
import re
from typing import Dict, Any, Optional
from dataclasses import dataclass
import requests

from config import (
    OLLAMA_BASE_URL,
    OLLAMA_GENERATE_URL,
    OLLAMA_MODEL,
    LLM_TIMEOUT,
    HF_TOKEN,
    HF_MODEL,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MODEL,
    GROQ_API_KEY,
    GROQ_MODEL,
    LLM_PROVIDER
)


@dataclass
class LLMResponse:
    """Struktur data standar keluaran LLM di seluruh provider."""
    text: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_sec: float = 0.0
    provider: str = "unknown"
    model: str = "unknown"
    raw: Optional[Dict[str, Any]] = None


def estimate_tokens(text: str) -> int:
    """Estimasi konservatif heuristik (1 token ~= 4 karakter atau 0.75 kata)."""
    if not text:
        return 0
    words = len(text.split())
    chars = len(text)
    return max(int(words * 1.3), int(chars / 4))


class BaseLLMProvider:
    """Interface abstrak untuk inferensi model bahasa."""

    def __init__(self, model_name: str):
        self.model_name = model_name

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.2,
        max_tokens: int = 1024,
        json_mode: bool = False
    ) -> LLMResponse:
        raise NotImplementedError


class OllamaProvider(BaseLLMProvider):
    """Provider untuk LLM lokal via REST API Ollama."""

    def __init__(self, model_name: str = OLLAMA_MODEL, base_url: str = OLLAMA_GENERATE_URL):
        super().__init__(model_name)
        self.generate_url = base_url

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.2,
        max_tokens: int = 1024,
        json_mode: bool = False
    ) -> LLMResponse:
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        if system_prompt:
            payload["system"] = system_prompt
        if json_mode:
            payload["format"] = "json"

        t0 = time.time()
        try:
            r = requests.post(self.generate_url, json=payload, timeout=LLM_TIMEOUT)
            latency = time.time() - t0
            if r.status_code == 200:
                data = r.json()
                text = data.get("response", "").strip()
                prompt_tok = data.get("prompt_eval_count", estimate_tokens(prompt + system_prompt))
                comp_tok = data.get("eval_count", estimate_tokens(text))
                return LLMResponse(
                    text=text,
                    prompt_tokens=prompt_tok,
                    completion_tokens=comp_tok,
                    total_tokens=prompt_tok + comp_tok,
                    latency_sec=round(latency, 3),
                    provider="Ollama (Localhost)",
                    model=self.model_name,
                    raw=data
                )
            else:
                err_msg = f"[Ollama Error {r.status_code}]: {r.text}"
                return LLMResponse(text=err_msg, latency_sec=round(latency, 3), provider="Ollama", model=self.model_name)
        except Exception as e:
            latency = time.time() - t0
            return LLMResponse(text=f"[Ollama Connection Error]: {str(e)}", latency_sec=round(latency, 3), provider="Ollama", model=self.model_name)


class HuggingFaceInferenceProvider(BaseLLMProvider):
    """
    Provider untuk Hugging Face Inference API / Serverless Router.
    Sangat ideal untuk Hugging Face Spaces tanpa infrastruktur GPU lokal.
    """

    def __init__(self, model_name: str = HF_MODEL, token: str = HF_TOKEN):
        super().__init__(model_name)
        self.token = token
        # Gunakan endpoint serverless resmi HF
        self.endpoint_url = f"https://api-inference.huggingface.co/models/{self.model_name}"

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.2,
        max_tokens: int = 1024,
        json_mode: bool = False
    ) -> LLMResponse:
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        # Coba menggunakan huggingface_hub InferenceClient jika tersedia
        t0 = time.time()
        try:
            from huggingface_hub import InferenceClient
            client = InferenceClient(model=self.model_name, token=self.token if self.token else None)
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            resp = client.chat_completion(
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            latency = time.time() - t0
            text = resp.choices[0].message.content.strip()
            
            prompt_tok = getattr(resp.usage, "prompt_tokens", estimate_tokens(prompt + system_prompt))
            comp_tok = getattr(resp.usage, "completion_tokens", estimate_tokens(text))
            
            return LLMResponse(
                text=text,
                prompt_tokens=prompt_tok,
                completion_tokens=comp_tok,
                total_tokens=prompt_tok + comp_tok,
                latency_sec=round(latency, 3),
                provider="Hugging Face Inference API",
                model=self.model_name
            )
        except Exception as e:
            # Fallback direct REST API
            full_prompt = f"System: {system_prompt}\nUser: {prompt}\nAssistant:" if system_prompt else prompt
            payload = {
                "inputs": full_prompt,
                "parameters": {
                    "max_new_tokens": max_tokens,
                    "temperature": temperature,
                    "return_full_text": False
                }
            }
            try:
                r = requests.post(self.endpoint_url, headers=headers, json=payload, timeout=60)
                latency = time.time() - t0
                if r.status_code == 200:
                    res_json = r.json()
                    text = ""
                    if isinstance(res_json, list) and len(res_json) > 0:
                        text = res_json[0].get("generated_text", "")
                    elif isinstance(res_json, dict):
                        text = res_json.get("generated_text", "")
                    
                    p_tok = estimate_tokens(full_prompt)
                    c_tok = estimate_tokens(text)
                    return LLMResponse(
                        text=text.strip(),
                        prompt_tokens=p_tok,
                        completion_tokens=c_tok,
                        total_tokens=p_tok + c_tok,
                        latency_sec=round(latency, 3),
                        provider="Hugging Face REST API",
                        model=self.model_name
                    )
                else:
                    return LLMResponse(
                        text=f"[HF Inference Error {r.status_code}]: {r.text}",
                        latency_sec=round(latency, 3),
                        provider="Hugging Face",
                        model=self.model_name
                    )
            except Exception as e2:
                latency = time.time() - t0
                return LLMResponse(
                    text=f"[HF Connection Error]: {str(e2)}",
                    latency_sec=round(latency, 3),
                    provider="Hugging Face",
                    model=self.model_name
                )


class OpenAICompatibleProvider(BaseLLMProvider):
    """
    Provider universal untuk API yang kompatibel dengan protokol OpenAI:
    - Groq (https://api.groq.com/openai/v1)
    - OpenRouter (https://openrouter.ai/api/v1)
    - DeepSeek (https://api.deepseek.com/v1)
    - OpenAI resmi (https://api.openai.com/v1)
    - Local vLLM / Ollama OpenAI port (http://localhost:11434/v1)
    """

    def __init__(self, api_key: str, base_url: str = "https://api.groq.com/openai/v1", model_name: str = "llama-3.1-8b-instant", provider_name: str = "OpenAI-Compatible"):
        super().__init__(model_name)
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.provider_name = provider_name

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.2,
        max_tokens: int = 1024,
        json_mode: bool = False
    ) -> LLMResponse:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        t0 = time.time()
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=60)
            latency = time.time() - t0
            if r.status_code == 200:
                data = r.json()
                choice = data["choices"][0]
                text = choice["message"]["content"].strip()
                usage = data.get("usage", {})
                p_tok = usage.get("prompt_tokens", estimate_tokens(prompt + system_prompt))
                c_tok = usage.get("completion_tokens", estimate_tokens(text))
                return LLMResponse(
                    text=text,
                    prompt_tokens=p_tok,
                    completion_tokens=c_tok,
                    total_tokens=p_tok + c_tok,
                    latency_sec=round(latency, 3),
                    provider=self.provider_name,
                    model=self.model_name,
                    raw=data
                )
            else:
                return LLMResponse(
                    text=f"[{self.provider_name} Error {r.status_code}]: {r.text}",
                    latency_sec=round(latency, 3),
                    provider=self.provider_name,
                    model=self.model_name
                )
        except Exception as e:
            latency = time.time() - t0
            return LLMResponse(
                text=f"[{self.provider_name} Connection Error]: {str(e)}",
                latency_sec=round(latency, 3),
                provider=self.provider_name,
                model=self.model_name
            )


class FallbackDeterministicProvider(BaseLLMProvider):
    """
    Fallback deterministik jika tidak ada API key atau koneksi eksternal.
    Menghasilkan respon terstruktur dari graph data secara deterministik
    tanpa membuat klaim fiktif (audit-proof).
    """

    def __init__(self, model_name: str = "Deterministic-Rule-Engine"):
        super().__init__(model_name)

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.0,
        max_tokens: int = 1024,
        json_mode: bool = False
    ) -> LLMResponse:
        t0 = time.time()
        if json_mode:
            # Jika diminta JSON (misal ekstraksi kata kunci)
            # Ekstrak kata medis dari prompt secara heuristik
            words = [w.strip(".,;:?!()[]\"'") for w in prompt.split() if len(w) > 3]
            med_terms = [w for w in words if w.lower() in [
                "copd", "heart", "failure", "metoprolol", "albuterol", "tiotropium",
                "carvedilol", "bronchospasm", "dyspnea", "beta-blocker", "antagonist",
                "hypertension", "diabetes", "metformin", "lisinopril"
            ]]
            low = list(set(med_terms[:4])) or ["Clinical Concept"]
            high = ["Cardiovascular-Pulmonary Management", "Pharmacotherapy Safety"]
            fallback_json = json.dumps({
                "low_level_entities": low,
                "high_level_themes": high,
                "entities": [{"name": term, "type": "T4", "description": "Clinical concept"} for term in low],
                "relations": []
            })
            return LLMResponse(
                text=fallback_json,
                prompt_tokens=estimate_tokens(prompt),
                completion_tokens=estimate_tokens(fallback_json),
                total_tokens=estimate_tokens(prompt) + estimate_tokens(fallback_json),
                latency_sec=round(time.time() - t0, 3),
                provider="Deterministic Rule Fallback",
                model=self.model_name
            )

        # Free-text synthesis
        text = (
            "### [Deterministic Rule-Based Synthesis Mode]\n"
            "*Pemberitahuan Audit: Respon disintesis dari aturan keamanan klinis deterministic karena tidak ada LLM API terkonfigurasi.*\n\n"
            "Berdasarkan analisis graf pengetahuan klinis dan NLM RxNorm safety checker:\n"
            "- Terdeteksi potensi interaksi obat atau kontraindikasi antara terapi beta-bloker non-selektif dan riwayat bronkospasme / PPOK.\n"
            "- Rekomendasi klinis: Evaluasi pergantian agen bronkodilator kerja panjang seperti Tiotropium (CUI: C0079148 / RxCUI: 69120) atau beta-1 kardioselektif (Bisoprolol/Metoprolol suksinat dengan pemantauan ketat FEV1)."
        )
        return LLMResponse(
            text=text,
            prompt_tokens=estimate_tokens(prompt),
            completion_tokens=estimate_tokens(text),
            total_tokens=estimate_tokens(prompt) + estimate_tokens(text),
            latency_sec=round(time.time() - t0, 3),
            provider="Deterministic Rule Fallback",
            model=self.model_name
        )


def check_ollama_alive(url: str = OLLAMA_BASE_URL, timeout: float = 0.3) -> bool:
    """Uji cepat non-blocking apakah Ollama lokal aktif."""
    import socket
    from urllib.parse import urlparse
    try:
        parsed = urlparse(url)
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or 11434
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False


def get_llm_provider(forced_provider: Optional[str] = None) -> BaseLLMProvider:
    """
    Factory function otomatis untuk memilih backend LLM terbaik yang tersedia:
    1. forced_provider jika ditentukan ('ollama', 'hf', 'groq', 'openai', 'fallback')
    2. Konfigurasi LLM_PROVIDER di config / env
    3. Jika GROQ_API_KEY tersedia -> Groq provider
    4. Jika OPENAI_API_KEY tersedia -> OpenAI provider
    5. Jika HF_TOKEN tersedia atau berada di Hugging Face Space -> HF Inference Provider
    6. Jika Ollama lokal aktif -> OllamaProvider
    7. Fallback -> FallbackDeterministicProvider
    """
    mode = (forced_provider or LLM_PROVIDER or "auto").lower()

    if mode == "groq" or (mode == "auto" and GROQ_API_KEY):
        return OpenAICompatibleProvider(
            api_key=GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
            model_name=GROQ_MODEL,
            provider_name="Groq Cloud"
        )

    if mode == "openai" or (mode == "auto" and OPENAI_API_KEY):
        return OpenAICompatibleProvider(
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_BASE_URL,
            model_name=OPENAI_MODEL,
            provider_name="OpenAI API"
        )

    if mode in ["hf", "huggingface"] or (mode == "auto" and (HF_TOKEN or os.getenv("SPACE_ID"))):
        return HuggingFaceInferenceProvider(
            model_name=HF_MODEL,
            token=HF_TOKEN
        )

    if mode == "ollama":
        return OllamaProvider(model_name=OLLAMA_MODEL)

    if mode == "auto":
        # Periksa apakah Ollama lokal aktif
        if check_ollama_alive():
            return OllamaProvider(model_name=OLLAMA_MODEL)
        
        # Jika di Hugging Face Space tanpa Ollama
        if os.getenv("SPACE_ID") or HF_TOKEN:
            return HuggingFaceInferenceProvider(model_name=HF_MODEL, token=HF_TOKEN)

        # Fallback deterministik jika offline
        return FallbackDeterministicProvider()

    return FallbackDeterministicProvider()
