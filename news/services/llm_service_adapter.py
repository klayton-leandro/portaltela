import threading
import requests
import os

from typing import Optional
from domain.interfaces import LLMServiceInterface
from domain.entities import LLMResult
from services.llm_service import LLMService as OriginalLLMService


class LLMServiceSingleton:
    """Singleton thread-safe para LLMService"""
    _instance: Optional[OriginalLLMService] = None
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> OriginalLLMService:
        """Retorna instância única do LLMService"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = OriginalLLMService()
        return cls._instance

    @classmethod
    def clear(cls):
        """Limpa a instância cacheada"""
        with cls._lock:
            cls._instance = None


class LLMServiceAdapter(LLMServiceInterface):
    """
    Adapter que implementa LLMServiceInterface usando o LLMService original
    Permite inversão de dependência sem reescrever toda a lógica
    Usa Singleton para reutilizar instância
    """

    def __init__(self, use_cache: bool = True, **kwargs):
        """
        Inicializa o adapter

        Args:
            use_cache: Se True, usa Singleton
            **kwargs: Argumentos adicionais para o LLMService
        """
        if use_cache:
            self._service = LLMServiceSingleton.get_instance()
        else:
            self._service = OriginalLLMService(**kwargs)

    def process_content(self, content: str, title: str, subtitle: str) -> LLMResult:
        """
        Processa conteúdo usando o LLMService original

        Args:
            content: Conteúdo da notícia
            title: Título
            subtitle: Subtítulo

        Returns:
            LLMResult com o resultado do processamento
        """
        # Chama o serviço original
        original_result = self._service.process_content(
            content=content,
            title=title,
            subtitle=subtitle
        )

        # Converte para o formato da interface
        return LLMResult(
            resumo=original_result.resumo,
            status=original_result.status,
            raw_response=original_result.raw_response
        )

    @staticmethod
    def is_llm_available() -> bool:
        """Verifica se o LLM Studio está disponível"""

        api_url = os.environ.get(
            "LM_API_URL", "http://localhost:1234/api/v1/chat")
        api_token = os.environ.get("LM_API_TOKEN", "")
        # Tenta endpoint de models do LM Studio
        models_url = api_url.replace(
            "/chat", "/models").replace("/v1/chat", "/v1/models")

        headers = {}
        if api_token:
            headers["Authorization"] = f"Bearer {api_token}"

        try:
            response = requests.get(models_url, headers=headers, timeout=5)
            return response.status_code == 200
        except:
            return False

    @staticmethod
    def get_loaded_model() -> Optional[str]:
        """Retorna o modelo atualmente carregado no LM Studio"""

        api_url = os.environ.get(
            "LM_API_URL", "http://localhost:1234/api/v1/chat")
        api_token = os.environ.get("LM_API_TOKEN", "")
        models_url = api_url.replace(
            "/chat", "/models").replace("/v1/chat", "/v1/models")

        headers = {}
        if api_token:
            headers["Authorization"] = f"Bearer {api_token}"

        try:
            response = requests.get(models_url, headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and len(data['data']) > 0:
                    return data['data'][0].get('id', 'unknown')
            return None
        except:
            return None

    @staticmethod
    def clear_cache():
        """Limpa a instância cacheada do LLMService"""
        LLMServiceSingleton.clear()
