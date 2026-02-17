from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

from domain.entities import LLMResult


class NewsRepositoryInterface(ABC):
    """Interface para repositório de notícias"""

    @abstractmethod
    def save(self, news_data: Dict[str, Any]) -> str:
        """
        Salva uma notícia no repositório

        Args:
            news_data: Dados da notícia

        Returns:
            ID do documento salvo
        """
        pass

    @abstractmethod
    def find_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Busca uma notícia pela URL

        Args:
            url: URL da notícia

        Returns:
            Dados da notícia ou None
        """
        pass

    @abstractmethod
    def update_by_url(self, url: str, news_data: Dict[str, Any]) -> bool:
        """
        Atualiza uma notícia existente

        Args:
            url: URL da notícia
            news_data: Novos dados

        Returns:
            True se atualizou, False se não encontrou
        """
        pass

    @abstractmethod
    def upsert(self, url: str, news_data: Dict[str, Any]) -> str:
        """
        Insere ou atualiza uma notícia

        Args:
            url: URL da notícia (chave única)
            news_data: Dados da notícia

        Returns:
            ID do documento
        """
        pass

    @abstractmethod
    def list_recent(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Lista as notícias mais recentes"""
        pass


class LLMServiceInterface(ABC):
    """Interface para serviço de LLM"""

    @abstractmethod
    def process_content(self, content: str, title: str, subtitle: str) -> LLMResult:
        """
        Processa conteúdo de notícia com LLM

        Args:
            content: Conteúdo da notícia
            title: Título da notícia
            subtitle: Subtítulo

        Returns:
            LLMResult com resumo
        """
        pass
