from abc import ABC, abstractmethod
from typing import Optional

from domain.entities import NewsArticle


class ScraperInterface(ABC):
    """Interface abstrata para scrapers de portais de notícias"""

    @abstractmethod
    def scrape(self, url: str) -> Optional[NewsArticle]:
        """
        Extrai dados de uma notícia a partir da URL

        Args:
            url: URL da notícia

        Returns:
            NewsArticle com os dados extraídos ou None se falhar
        """
        pass

    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """
        Verifica se este scraper pode processar a URL

        Args:
            url: URL para verificar

        Returns:
            True se o scraper pode processar esta URL
        """
        pass

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Retorna o nome da fonte (ex: 'g1', 'uol', 'folha')"""
        pass
