import os
import time
import requests
from typing import Optional, Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv

try:
    from core.logging import log
except ImportError:
    from loguru import logger as log

load_dotenv(override=False)


@dataclass
class LLMResponse:
    """Resposta processada pela LLM"""
    resumo: str
    status: str
    raw_response: Optional[Dict[str, Any]] = None


class LLMService:
    """Serviço para resumir notícias via LM Studio local"""

    DEFAULT_API_URL = "http://localhost:1234/api/v1/chat"
    DEFAULT_MODEL = "phi-3-mini-4k-instruct"
    DEFAULT_TIMEOUT = 60
    DEFAULT_MAX_RETRIES = 1
    MAX_CONTENT_LENGTH = 4000  # Limite para reduzir latência

    def __init__(self, api_url: str = None, model: str = None):
        self.api_url = api_url or os.environ.get(
            "LM_API_URL", self.DEFAULT_API_URL)
        self.model = model or os.environ.get("LM_MODEL", self.DEFAULT_MODEL)
        self.api_token = os.environ.get("LM_API_TOKEN", "")
        self.timeout = int(os.environ.get("LM_TIMEOUT", self.DEFAULT_TIMEOUT))
        self.max_retries = int(os.environ.get(
            "LM_MAX_RETRIES", self.DEFAULT_MAX_RETRIES))

    def process_content(self, content: str, title: str = "", subtitle: str = "") -> LLMResponse:
        """
        Gera resumo da notícia usando LLM local.

        Args:
            content: Conteúdo da notícia
            title: Título da notícia
            subtitle: Subtítulo da notícia

        Returns:
            LLMResponse com resumo gerado
        """
        truncated = self._truncate(content)

        prompt = f"Resuma em até 3 frases:\n\nTítulo: {title}\n\n{truncated}"

        payload = {
            "model": self.model,
            "input": prompt,
            "system_prompt": "Você resume notícias de forma concisa.",
            "temperature": 0,
            "max_output_tokens": 150,
            "stream": False,
            "store": False
        }

        headers = {"Content-Type": "application/json"}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"

        try:
            response = self._send_request(headers, payload)

            if response.status_code == 200:
                result = response.json()
                resumo = self._extract_text(result)
                log.success(f"Resumo gerado ({len(resumo)} chars)")
                return LLMResponse(resumo=resumo, status="success", raw_response=result)

            log.error(f"Erro na API: {response.status_code}")
            return LLMResponse(
                resumo=self._fallback_summary(title, subtitle, content),
                status=f"error:{response.status_code}"
            )

        except requests.exceptions.ReadTimeout:
            log.warning(f"Timeout após {self.timeout}s")
            return LLMResponse(
                resumo=self._fallback_summary(title, subtitle, content),
                status="timeout"
            )
        except requests.exceptions.ConnectionError:
            log.warning("LLM indisponível")
            return LLMResponse(
                resumo=self._fallback_summary(title, subtitle, content),
                status="unavailable"
            )
        except Exception as e:
            log.exception(f"Erro: {e}")
            return LLMResponse(
                resumo=self._fallback_summary(title, subtitle, content),
                status=f"error:{e}"
            )

    def _send_request(self, headers: dict, payload: dict) -> requests.Response:
        """Envia request com retry simples."""
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    wait = 2 ** attempt
                    log.warning(f"Retry {attempt + 1} em {wait}s...")
                    time.sleep(wait)

                return requests.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )
            except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
                last_error = e
                if attempt == self.max_retries:
                    raise
        raise last_error

    def _truncate(self, content: str) -> str:
        """Limita conteúdo para reduzir latência."""
        if len(content) <= self.MAX_CONTENT_LENGTH:
            return content
        log.info(
            f"Conteúdo truncado: {len(content)} -> {self.MAX_CONTENT_LENGTH}")
        return content[:self.MAX_CONTENT_LENGTH]

    def _extract_text(self, result: Dict[str, Any]) -> str:
        """Extrai texto da resposta LM Studio."""
        # Formato LM Studio /api/v1/chat
        if "output" in result:
            for item in result["output"]:
                if item.get("type") == "message":
                    return item.get("content", "").strip()

        # Formatos alternativos
        if "choices" in result:
            return result["choices"][0].get("message", {}).get("content", "").strip()
        if "content" in result:
            return result["content"].strip()
        if "response" in result:
            return result["response"].strip()

        return str(result)

    def _fallback_summary(self, title: str, subtitle: str, content: str) -> str:
        """Gera resumo básico sem LLM."""
        if subtitle:
            return f"{title}. {subtitle}"
        sentences = content.split(".")
        if len(sentences) >= 2:
            return f"{sentences[0].strip()}. {sentences[1].strip()}."
        return content[:200]
