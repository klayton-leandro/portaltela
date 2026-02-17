from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class LLMResult:
    """Resultado do processamento LLM"""
    resumo: str
    status: str
    raw_response: Optional[Dict[str, Any]] = None

    def is_success(self) -> bool:
        """Verifica se o processamento foi bem-sucedido"""
        return self.status == "success"

    def is_fallback(self) -> bool:
        """Verifica se usou fallback"""
        return self.status in ("timeout", "unavailable")
