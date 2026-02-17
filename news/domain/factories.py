from typing import Optional
from domain.interfaces import ScraperInterface, NewsRepositoryInterface, LLMServiceInterface
from domain.usecases import ProcessNewsUseCase


class UseCaseFactory:
    """Factory para criar Use Cases com dependências injetadas"""

    @staticmethod
    def create_process_news_usecase(
        schema_name: str = "g1",
        scraper: Optional[ScraperInterface] = None,
        repository: Optional[NewsRepositoryInterface] = None,
        llm_service: Optional[LLMServiceInterface] = None
    ) -> ProcessNewsUseCase:
        """
        Cria um ProcessNewsUseCase com dependências

        Args:
            schema_name: Nome do schema para o LLM
            scraper: Scraper customizado (opcional)
            repository: Repository customizado (opcional)
            llm_service: LLM Service customizado (opcional)

        Returns:
            ProcessNewsUseCase configurado
        """
        # Scraper padrão: G1 (passa schema_name para configuração)
        if scraper is None:
            from scraper.g1_scraper import G1Scraper
            scraper = G1Scraper(schema_name=schema_name)

        # Repository padrão: MongoDB
        if repository is None:
            from infra.mongo_news_repository import MongoNewsRepository
            repository = MongoNewsRepository()

        # LLM Service padrão
        if llm_service is None:
            from services.llm_service_adapter import LLMServiceAdapter
            llm_service = LLMServiceAdapter()

        return ProcessNewsUseCase(
            scraper=scraper,
            llm_service=llm_service,
            repository=repository
        )


class ScraperFactory:
    """Factory para criar scrapers baseado na URL"""

    _scrapers = {}

    @classmethod
    def register(cls, scraper_class):
        """Registra um scraper"""
        scraper = scraper_class()
        cls._scrapers[scraper.source_name] = scraper_class
        return scraper_class

    @classmethod
    def get_scraper_for_url(cls, url: str) -> Optional[ScraperInterface]:
        """
        Retorna o scraper apropriado para a URL

        Args:
            url: URL da notícia

        Returns:
            Scraper que pode processar a URL ou None
        """
        # Lazy loading dos scrapers conhecidos
        if not cls._scrapers:
            from scraper.g1_scraper import G1Scraper
            cls._scrapers['g1'] = G1Scraper
            # Adicione outros scrapers aqui

        for source_name, scraper_class in cls._scrapers.items():
            scraper = scraper_class()
            if scraper.can_handle(url):
                return scraper

        return None

    @classmethod
    def list_available_sources(cls) -> list:
        """Lista fontes disponíveis"""
        if not cls._scrapers:
            from scraper.g1_scraper import G1Scraper
            cls._scrapers['g1'] = G1Scraper

        return list(cls._scrapers.keys())
