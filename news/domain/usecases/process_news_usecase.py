from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any

from domain.interfaces import (
    ScraperInterface,
    NewsRepositoryInterface,
    LLMServiceInterface
)

try:
    from core.logging import log
except ImportError:
    from loguru import logger as log


@dataclass
class ProcessNewsInput:
    """Input para o caso de uso de processar notícia"""
    url: str
    schema_name: str = "g1"
    task_id: Optional[str] = None


@dataclass
class ProcessNewsOutput:
    """Output do caso de uso de processar notícia"""
    status: str
    mongodb_id: Optional[str] = None
    url: Optional[str] = None
    title: Optional[str] = None
    schema_used: Optional[str] = None
    llm_status: Optional[str] = None
    resumo: Optional[str] = None
    error: Optional[str] = None
    article: Optional[Dict[str, Any]] = None


class ProcessNewsUseCase:
    """
    Use Case para processar uma notícia

    Orquestra o fluxo:
    1. Extração via Scraper
    2. Processamento via LLM
    3. Persistência no Repository
    """

    def __init__(
        self,
        scraper: ScraperInterface,
        llm_service: LLMServiceInterface,
        repository: NewsRepositoryInterface
    ):
        """
        Injeta dependências via construtor (Dependency Injection)

        Args:
            scraper: Implementação de ScraperInterface
            llm_service: Implementação de LLMServiceInterface
            repository: Implementação de NewsRepositoryInterface
        """
        self._scraper = scraper
        self._llm_service = llm_service
        self._repository = repository

    def execute(self, input_data: ProcessNewsInput) -> ProcessNewsOutput:
        """
        Executa o processamento da notícia

        Args:
            input_data: Dados de entrada

        Returns:
            ProcessNewsOutput com resultado do processamento
        """
        task_id = input_data.task_id or "no-task"
        log.info(
            f"[UseCase {task_id}] Iniciando processamento: {input_data.url}")

        try:
            # 1. Verifica se o scraper pode processar esta URL
            if not self._scraper.can_handle(input_data.url):
                return ProcessNewsOutput(
                    status="error",
                    url=input_data.url,
                    error=f"URL não suportada pelo scraper {self._scraper.source_name}"
                )

            # 2. Extrai a notícia
            log.info(f"[UseCase {task_id}] Extraindo notícia...")
            article = self._scraper.scrape(input_data.url)

            if not article:
                return ProcessNewsOutput(
                    status="error",
                    url=input_data.url,
                    error="Não foi possível extrair a notícia"
                )

            log.info(f"[UseCase {task_id}] Notícia extraída: {article.title}")

            # 3. Processa com LLM
            log.info(f"[UseCase {task_id}] Processando com LLM...")
            llm_result = self._llm_service.process_content(
                content=article.content,
                title=article.title,
                subtitle=article.subtitle or ""
            )

            log.info(f"[UseCase {task_id}] LLM Status: {llm_result.status}")

            # 4. Prepara documento para persistência
            document = {
                "title": article.title,
                "subtitle": article.subtitle,
                "content": article.content,
                "summary": llm_result.resumo,
                "llm_status": llm_result.status,
                "author": article.author,
                "pub_date": article.pub_date,
                "url": article.url,
                "images": article.images,
                "source": article.source or self._scraper.source_name,
                "schema_used": input_data.schema_name,
                "task_id": input_data.task_id
            }

            # 5. Persiste no repositório (upsert)
            log.info(f"[UseCase {task_id}] Salvando no repositório...")
            result_id = self._repository.upsert(article.url, document)

            log.info(
                f"[UseCase {task_id}] Processamento concluído: {result_id}")

            return ProcessNewsOutput(
                status="success",
                mongodb_id=result_id,
                url=article.url,
                title=article.title,
                schema_used=input_data.schema_name,
                llm_status=llm_result.status,
                resumo=llm_result.resumo,
                article=asdict(article)
            )

        except Exception as e:
            log.exception(f"[UseCase {task_id}] Erro: {e}")
            return ProcessNewsOutput(
                status="error",
                url=input_data.url,
                error=str(e)
            )
