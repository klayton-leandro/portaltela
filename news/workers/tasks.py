from celery import shared_task

from core.config import settings
from core.logging import log
from domain.factories import UseCaseFactory
from domain.usecases import ProcessNewsInput
from services.wordpress_publisher import WordPressPublisherService
from infra.mongo_news_repository import MongoNewsRepository
from infra.mongo_news_repository import MongoNewsRepository
from services.wordpress_publisher import WordPressPublisherService
from infra.mongo_news_repository import MongoNewsRepository


@shared_task(
    bind=True,
    name="workers.tasks.process_news_url",
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
)
def process_news_url(self, url: str, schema_name: str = "g1") -> dict:
    """
    Task para processar uma URL de notícia de forma assíncrona

    Args:
        url: URL da notícia a ser processada
        schema_name: Nome do schema YAML (sem extensão) para o prompt da LLM

    Returns:
        Dicionário com o resultado do processamento
    """
    task_id = self.request.id
    log.info(f"[Task {task_id}] Iniciando processamento: {url}")

    try:
        # Cria Use Case via Factory (Dependency Injection)
        use_case = UseCaseFactory.create_process_news_usecase(
            schema_name=schema_name
        )

        # Prepara input
        input_data = ProcessNewsInput(
            url=url,
            schema_name=schema_name,
            task_id=task_id
        )

        # Executa o Use Case
        output = use_case.execute(input_data)

        if output.status == "error":
            log.error(f"[Task {task_id}] Erro: {output.error}")
            return {
                "status": "error",
                "task_id": task_id,
                "message": output.error,
                "url": url
            }

        log.info(f"[Task {task_id}] Processamento concluído com sucesso")

        return {
            "status": output.status,
            "task_id": task_id,
            "mongodb_id": output.mongodb_id,
            "url": url,
            "title": output.title,
            "schema_used": output.schema_used,
            "llm_processing": {
                "status": output.llm_status,
                "resumo": output.resumo,
            },
            "article": output.article
        }

    except Exception as e:
        log.exception(f"[Task {task_id}] Erro no processamento: {e}")
        raise


@shared_task(
    bind=True,
    name="workers.tasks.process_news_batch",
    max_retries=1,
)
def process_news_batch(self, urls: list, schema_name: str = "g1") -> dict:
    """
    Task para processar múltiplas URLs de notícias

    Args:
        urls: Lista de URLs para processar
        schema_name: Nome do schema YAML para todas as URLs

    Returns:
        Dicionário com IDs das tasks criadas
    """
    task_id = self.request.id
    log.info(f"[Batch {task_id}] Iniciando batch com {len(urls)} URLs")

    task_ids = []
    for url in urls:
        # Cria uma task para cada URL
        task = process_news_url.delay(url, schema_name)
        task_ids.append({
            "url": url,
            "task_id": task.id
        })
        log.info(f"[Batch {task_id}] Task criada: {task.id} para {url}")

    return {
        "status": "batch_queued",
        "batch_task_id": task_id,
        "total_urls": len(urls),
        "tasks": task_ids,
        "schema_used": schema_name
    }


@shared_task(name="workers.tasks.health_check")
def health_check() -> dict:
    """Task de health check para verificar se o worker está funcionando"""
    log.info("Health check executado")
    return {
        "status": "healthy",
        "available_schemas": settings.list_schemas()
    }


@shared_task(
    bind=True,
    name="workers.tasks.publish_to_wordpress",
    max_retries=3,
    default_retry_delay=30,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def publish_to_wordpress(self, mongodb_id: str) -> dict:
    """
    Task para publicar uma notícia do MongoDB no WordPress

    Args:
        mongodb_id: ID do documento no MongoDB

    Returns:
        Dicionário com resultado da publicação
    """

    task_id = self.request.id
    log.info(f"[Task {task_id}] Publicando notícia: {mongodb_id}")

    try:
        # Busca notícia no MongoDB
        repo = MongoNewsRepository()
        news = repo.find_by_id(mongodb_id)

        if not news:
            return {
                "status": "error",
                "task_id": task_id,
                "mongodb_id": mongodb_id,
                "error": "Notícia não encontrada no MongoDB"
            }

        # Verifica se já foi publicada
        if news.get("wordpress_published"):
            return {
                "status": "already_published",
                "task_id": task_id,
                "mongodb_id": mongodb_id,
                "wordpress_post_id": news.get("wordpress_post_id"),
                "wordpress_url": news.get("wordpress_url")
            }

        # Publica no WordPress
        publisher = WordPressPublisherService()
        result = publisher.publish_from_processed_news(news)

        if result.success:
            # Atualiza status no MongoDB
            repo.mark_as_published(
                mongodb_id,
                post_id=result.post_id,
                post_url=result.post_url
            )

            log.success(
                f"[Task {task_id}] Publicado com sucesso: Post ID {result.post_id}")
            return {
                "status": "published",
                "task_id": task_id,
                "mongodb_id": mongodb_id,
                "wordpress_post_id": result.post_id,
                "wordpress_url": result.post_url
            }
        else:
            # Marca erro no MongoDB
            repo.mark_publish_error(mongodb_id, result.error)

            return {
                "status": "error",
                "task_id": task_id,
                "mongodb_id": mongodb_id,
                "error": result.error
            }

    except Exception as e:
        log.exception(f"[Task {task_id}] Erro ao publicar: {e}")
        raise


@shared_task(
    bind=True,
    name="workers.tasks.publish_batch_to_wordpress",
    max_retries=1,
)
def publish_batch_to_wordpress(
    self,
    mongodb_ids: list = None,
    publish_pending: bool = False,
    limit: int = 50
) -> dict:
    """
    Task para publicar múltiplas notícias no WordPress

    Args:
        mongodb_ids: Lista de IDs do MongoDB para publicar
        publish_pending: Se True, busca notícias pendentes de publicação
        limit: Limite de notícias a publicar quando publish_pending=True

    Returns:
        Dicionário com IDs das tasks criadas
    """

    task_id = self.request.id
    log.info(f"[Batch Publish {task_id}] Iniciando batch publish")

    repo = MongoNewsRepository()
    task_ids = []

    # Se publish_pending, busca notícias não publicadas
    if publish_pending:
        pending_news = repo.find_pending_publish(limit=limit)
        mongodb_ids = [news["_id"] for news in pending_news]
        log.info(
            f"[Batch Publish {task_id}] Encontradas {len(mongodb_ids)} notícias pendentes")

    if not mongodb_ids:
        return {
            "status": "no_items",
            "batch_task_id": task_id,
            "message": "Nenhuma notícia para publicar"
        }

    # Cria task para cada notícia
    for mongodb_id in mongodb_ids:
        task = publish_to_wordpress.delay(str(mongodb_id))
        task_ids.append({
            "mongodb_id": str(mongodb_id),
            "task_id": task.id
        })
        log.info(
            f"[Batch Publish {task_id}] Task criada: {task.id} para {mongodb_id}")

    return {
        "status": "batch_queued",
        "batch_task_id": task_id,
        "total": len(task_ids),
        "tasks": task_ids
    }


@shared_task(
    bind=True,
    name="workers.tasks.process_and_publish",
    max_retries=3,
    default_retry_delay=60,
)
def process_and_publish(self, url: str, schema_name: str = "g1") -> dict:
    """
    Task que processa uma URL E publica no WordPress automaticamente

    Args:
        url: URL da notícia
        schema_name: Nome do schema YAML

    Returns:
        Dicionário com resultado completo
    """

    task_id = self.request.id
    log.info(f"[Task {task_id}] Processando e publicando: {url}")

    try:
        # 1. Processa a notícia
        use_case = UseCaseFactory.create_process_news_usecase(
            schema_name=schema_name
        )

        input_data = ProcessNewsInput(
            url=url,
            schema_name=schema_name,
            task_id=task_id
        )

        output = use_case.execute(input_data)

        if output.status == "error":
            return {
                "status": "processing_error",
                "task_id": task_id,
                "url": url,
                "error": output.error
            }

        # 2. Prepara dados para publicação
        processed_data = {
            "status": output.status,
            "mongodb_id": output.mongodb_id,
            "url": output.url,
            "title": output.title,
            "schema_used": output.schema_used,
            "llm_processing": {
                "status": output.llm_status,
                "resumo": output.resumo
            },
            "article": output.article
        }

        # 3. Publica no WordPress
        publisher = WordPressPublisherService()
        result = publisher.publish_from_processed_news(processed_data)

        if result.success:
            # Atualiza MongoDB com status de publicação
            repo = MongoNewsRepository()
            repo.mark_as_published(
                output.mongodb_id,
                post_id=result.post_id,
                post_url=result.post_url
            )

            log.success(
                f"[Task {task_id}] Processado e publicado: Post ID {result.post_id}")
            return {
                "status": "published",
                "task_id": task_id,
                "url": url,
                "mongodb_id": output.mongodb_id,
                "title": output.title,
                "wordpress_post_id": result.post_id,
                "wordpress_url": result.post_url
            }
        else:
            return {
                "status": "publish_error",
                "task_id": task_id,
                "url": url,
                "mongodb_id": output.mongodb_id,
                "error": result.error
            }

    except Exception as e:
        log.exception(f"[Task {task_id}] Erro: {e}")
        raise
