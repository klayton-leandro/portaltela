import uvicorn

from contextlib import asynccontextmanager
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from celery.result import AsyncResult

from core.config import settings
from core.logging import log

from workers.celery_app import celery_app
from workers.tasks import process_news_url, process_news_batch, health_check, publish_batch_to_wordpress as batch_task, publish_to_wordpress, process_and_publish


from domain.factories import UseCaseFactory, ScraperFactory
from domain.usecases import ProcessNewsInput

from services.wordpress_publisher import WordPressPublisherService
from services.llm_service_adapter import LLMServiceAdapter

from infra.mongo_news_repository import MongoNewsRepository


# Pydantic Models para Request/Response
class ProcessNewsRequest(BaseModel):
    """Request para processar uma única notícia"""
    url: str = Field(..., description="URL da notícia")
    schema_name: str = Field(
        default="g1", description="Nome do schema YAML (sem extensão)")

    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Valida se a URL é suportada por algum scraper"""
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL deve começar com http:// ou https://')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://example.com/noticia/...",
                "schema_name": "g1, uol, folha, etc."
            }
        }


class ProcessBatchRequest(BaseModel):
    """Request para processar múltiplas notícias"""
    urls: List[str] = Field(..., min_length=1,
                            max_length=50, description="Lista de URLs")
    schema_name: str = Field(default="g1", description="Nome do schema YAML")


class TaskResponse(BaseModel):
    """Response com informações da task"""
    task_id: str
    status: str
    message: str


class TaskStatusResponse(BaseModel):
    """Response com status detalhado da task"""
    task_id: str
    status: str
    result: Optional[dict] = None
    error: Optional[str] = None


class SchemasResponse(BaseModel):
    """Response com lista de schemas disponíveis"""
    schemas: List[str]
    total: int


class SourcesResponse(BaseModel):
    """Response com lista de fontes suportadas"""
    sources: List[str]
    total: int


# Helper functions
def validate_schema(schema_name: str) -> None:
    """Valida se o schema existe, lança HTTPException se não"""
    available_schemas = settings.list_schemas()
    if schema_name not in available_schemas:
        raise HTTPException(
            status_code=400,
            detail=f"Schema '{schema_name}' não encontrado. Disponíveis: {available_schemas}"
        )


def validate_url_source(url: str) -> None:
    """Valida se a URL é suportada por algum scraper"""
    scraper = ScraperFactory.get_scraper_for_url(url)
    if not scraper:
        available = ScraperFactory.list_available_sources()
        raise HTTPException(
            status_code=400,
            detail=f"URL não suportada. Fontes disponíveis: {available}"
        )


# Lifespan (substitui on_event deprecated)
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação"""
    # Startup
    log.info("API iniciada")
    log.info(f"Schemas disponíveis: {settings.list_schemas()}")
    log.info(f"Fontes disponíveis: {ScraperFactory.list_available_sources()}")
    yield
    # Shutdown
    log.info("API encerrada")


# Cria a aplicação FastAPI
app = FastAPI(
    title="News Feed API",
    description="API para extração e processamento assíncrono de notícias",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configura CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especifique os domínios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Endpoints

@app.get("/", tags=["Health"])
async def root():
    """Endpoint raiz"""
    return {
        "service": "News Feed API",
        "status": "running",
        "version": "2.0.0"
    }


@app.get("/health", tags=["Health"])
async def health():

    # Check Celery
    try:
        task = health_check.delay()
        result = task.get(timeout=5)
        celery_status = "healthy"
    except Exception as e:
        log.error(f"Celery health check falhou: {e}")
        celery_status = "unhealthy"
        result = {"error": str(e)}

    llm_available = LLMServiceAdapter.is_llm_available()
    llm_model = LLMServiceAdapter.get_loaded_model() if llm_available else None

    return {
        "api": "healthy",
        "celery": celery_status,
        "celery_result": result,
        "llm": {
            "status": "healthy" if llm_available else "unhealthy",
            "model": llm_model
        }
    }


@app.get("/health/llm", tags=["Health"])
async def health_llm():
    """Health check específico do LLM Studio"""

    available = LLMServiceAdapter.is_llm_available()
    model = LLMServiceAdapter.get_loaded_model() if available else None

    if not available:
        return {
            "status": "unhealthy",
            "message": "LLM Studio não está respondendo. Verifique se está rodando em localhost:1234",
            "model": None
        }

    return {
        "status": "healthy",
        "message": "LLM Studio está pronto para receber requisições",
        "model": model
    }


@app.get("/schemas", response_model=SchemasResponse, tags=["Schemas"])
async def list_schemas():
    """Lista todos os schemas de prompt disponíveis"""
    schemas = settings.list_schemas()
    return SchemasResponse(schemas=schemas, total=len(schemas))


@app.get("/sources", response_model=SourcesResponse, tags=["Schemas"])
async def list_sources():
    """Lista todas as fontes de notícias suportadas"""
    sources = ScraperFactory.list_available_sources()
    return SourcesResponse(sources=sources, total=len(sources))


@app.post("/process", response_model=TaskResponse, tags=["Process"])
async def process_news(request: ProcessNewsRequest):
    """
    Processa uma notícia de forma assíncrona

    - Valida a URL e o schema
    - Envia a URL para a fila de processamento
    - Retorna um task_id para consultar o status
    """
    log.info(f"Recebida requisição para processar: {request.url}")

    # Validações usando helpers
    validate_schema(request.schema_name)
    validate_url_source(request.url)

    # Envia para a fila
    task = process_news_url.delay(request.url, request.schema_name)

    log.info(f"Task criada: {task.id}")

    return TaskResponse(
        task_id=task.id,
        status="queued",
        message=f"Notícia enviada para processamento. Use /status/{task.id} para acompanhar."
    )


@app.post("/process/batch", response_model=TaskResponse, tags=["Process"])
async def process_news_batch_endpoint(request: ProcessBatchRequest):
    """
    Processa múltiplas notícias de forma assíncrona

    - Valida o schema e todas as URLs
    - Envia todas as URLs para a fila de processamento
    - Retorna um batch_task_id para consultar o status
    """
    log.info(f"Recebido batch com {len(request.urls)} URLs")

    # Valida o schema
    validate_schema(request.schema_name)

    # Valida todas as URLs
    unsupported_urls = []
    for url in request.urls:
        scraper = ScraperFactory.get_scraper_for_url(url)
        if not scraper:
            unsupported_urls.append(url)

    if unsupported_urls:
        raise HTTPException(
            status_code=400,
            detail=f"URLs não suportadas: {unsupported_urls}"
        )

    # Envia batch para a fila
    task = process_news_batch.delay(request.urls, request.schema_name)

    log.info(f"Batch task criada: {task.id}")

    return TaskResponse(
        task_id=task.id,
        status="batch_queued",
        message=f"{len(request.urls)} URLs enviadas para processamento."
    )


@app.get("/status/{task_id}", response_model=TaskStatusResponse, tags=["Status"])
async def get_task_status(task_id: str):
    """
    Consulta o status de uma task

    - PENDING: Task aguardando execução
    - STARTED: Task em execução
    - SUCCESS: Task concluída com sucesso
    - FAILURE: Task falhou
    - RETRY: Task sendo re-executada
    """
    task_result = AsyncResult(task_id, app=celery_app)

    response = TaskStatusResponse(
        task_id=task_id,
        status=task_result.status
    )

    if task_result.ready():
        if task_result.successful():
            response.result = task_result.result
        else:
            response.error = str(task_result.result)

    return response


@app.delete("/task/{task_id}", tags=["Status"])
async def revoke_task(task_id: str):
    """Cancela uma task pendente"""
    celery_app.control.revoke(task_id, terminate=True)
    log.info(f"Task {task_id} cancelada")

    return {
        "task_id": task_id,
        "status": "revoked",
        "message": "Task cancelada"
    }


@app.post("/process/sync", tags=["Process"])
async def process_news_sync(request: ProcessNewsRequest):
    """
    Processa uma notícia de forma SÍNCRONA (sem Celery/Redis)
    Útil para testes rápidos ou integração direta
    """
    log.info(f"[SYNC] Processando: {request.url}")

    # Validações
    validate_schema(request.schema_name)
    validate_url_source(request.url)

    try:

        use_case = UseCaseFactory.create_process_news_usecase(
            schema_name=request.schema_name
        )

        input_data = ProcessNewsInput(
            url=request.url,
            schema_name=request.schema_name,
            task_id="sync"
        )

        output = use_case.execute(input_data)

        if output.status == "error":
            raise HTTPException(status_code=400, detail=output.error)

        log.success(f"[SYNC] Processamento concluído: {output.mongodb_id}")

        return {
            "status": output.status,
            "mongodb_id": output.mongodb_id,
            "title": output.title,
            "schema_used": output.schema_used,
            "llm_processing": {
                "status": output.llm_status,
                "resumo": output.resumo
            },
            "article": output.article
        }

    except HTTPException:
        raise
    except Exception as e:
        log.exception(f"[SYNC] Erro: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/publish", tags=["WordPress"])
async def publish_to_wordpress(request: ProcessNewsRequest, category: str = None):
    """
    Processa uma notícia e publica diretamente no WordPress

    Este endpoint:
    1. Extrai e processa a notícia (scraping + LLM)
    2. Envia automaticamente para o webhook do WordPress

    Requer que as variáveis WORDPRESS_URL e WORDPRESS_API_KEY estejam configuradas.
    """
    log.info(f"[PUBLISH] Processando e publicando: {request.url}")

    # Validações
    validate_schema(request.schema_name)
    validate_url_source(request.url)

    try:
        # 1. Processa a notícia
        use_case = UseCaseFactory.create_process_news_usecase(
            schema_name=request.schema_name
        )

        input_data = ProcessNewsInput(
            url=request.url,
            schema_name=request.schema_name,
            task_id="publish"
        )

        output = use_case.execute(input_data)

        if output.status == "error":
            raise HTTPException(status_code=400, detail=output.error)

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
        result = publisher.publish_from_processed_news(
            processed_data, category)

        if not result.success:
            raise HTTPException(
                status_code=502,
                detail=f"Erro ao publicar no WordPress: {result.error}"
            )

        log.success(f"[PUBLISH] Post criado: ID {result.post_id}")

        return {
            "status": "published",
            "mongodb_id": output.mongodb_id,
            "wordpress": {
                "post_id": result.post_id,
                "post_url": result.post_url
            },
            "title": output.title,
            "llm_processing": {
                "status": output.llm_status,
                "resumo": output.resumo
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        log.exception(f"[PUBLISH] Erro: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class PublishBatchRequest(BaseModel):
    """Request para publicar múltiplas notícias em batch"""
    mongodb_ids: List[str] = Field(
        default=None,
        description="Lista de IDs do MongoDB para publicar"
    )
    publish_pending: bool = Field(
        default=False,
        description="Se True, publica todas as notícias pendentes"
    )
    limit: int = Field(
        default=50,
        le=100,
        description="Limite de notícias quando publish_pending=True"
    )


class ProcessAndPublishBatchRequest(BaseModel):
    """Request para processar e publicar múltiplas URLs"""
    urls: List[str] = Field(..., min_length=1, max_length=50)
    schema_name: str = Field(default="g1")


@app.post("/publish/batch", tags=["WordPress"])
async def publish_batch_to_wordpress(request: PublishBatchRequest):
    """
    Publica múltiplas notícias no WordPress via Celery

    Modos de operação:
    1. mongodb_ids: Lista específica de IDs para publicar
    2. publish_pending: True para publicar todas as notícias pendentes

    Retorna task_id para acompanhar o progresso via /status/{task_id}
    """

    log.info(f"[BATCH PUBLISH] Iniciando batch publish")

    if not request.mongodb_ids and not request.publish_pending:
        raise HTTPException(
            status_code=400,
            detail="Informe mongodb_ids ou defina publish_pending=true"
        )

    task = batch_task.delay(
        mongodb_ids=request.mongodb_ids,
        publish_pending=request.publish_pending,
        limit=request.limit
    )

    return TaskResponse(
        task_id=task.id,
        status="batch_queued",
        message=f"Batch de publicação enviado. Use /status/{task.id} para acompanhar."
    )


@app.post("/publish/from-db/{mongodb_id}", tags=["WordPress"])
async def publish_single_from_db(mongodb_id: str, async_mode: bool = True):
    """
    Publica uma notícia específica do MongoDB no WordPress

    Args:
        mongodb_id: ID do documento no MongoDB
        async_mode: Se True, usa Celery (retorna task_id). Se False, síncrono.
    """

    # Verifica se a notícia existe
    repo = MongoNewsRepository()
    news = repo.find_by_id(mongodb_id)

    if not news:
        raise HTTPException(status_code=404, detail="Notícia não encontrada")

    if news.get("wordpress_published"):
        return {
            "status": "already_published",
            "mongodb_id": mongodb_id,
            "wordpress_post_id": news.get("wordpress_post_id"),
            "wordpress_url": news.get("wordpress_url")
        }

    if async_mode:
        task = publish_to_wordpress.delay(mongodb_id)

        return TaskResponse(
            task_id=task.id,
            status="queued",
            message=f"Publicação enviada. Use /status/{task.id} para acompanhar."
        )
    else:
        # Modo síncrono
        publisher = WordPressPublisherService()
        result = publisher.publish_from_processed_news(news)

        if result.success:
            repo.mark_as_published(mongodb_id, result.post_id, result.post_url)
            return {
                "status": "published",
                "mongodb_id": mongodb_id,
                "wordpress_post_id": result.post_id,
                "wordpress_url": result.post_url
            }
        else:
            repo.mark_publish_error(mongodb_id, result.error)
            raise HTTPException(
                status_code=502,
                detail=f"Erro ao publicar: {result.error}"
            )


@app.post("/publish/process-and-publish", tags=["WordPress"])
async def process_and_publish_batch(request: ProcessAndPublishBatchRequest):
    """
    Processa múltiplas URLs e publica diretamente no WordPress

    Este endpoint combina scraping + LLM + publicação em uma única task por URL.
    Ideal para automação completa.
    """

    log.info(f"[PROCESS+PUBLISH] Batch com {len(request.urls)} URLs")

    # Valida schema
    validate_schema(request.schema_name)

    # Valida URLs
    unsupported_urls = []
    for url in request.urls:
        scraper = ScraperFactory.get_scraper_for_url(url)
        if not scraper:
            unsupported_urls.append(url)

    if unsupported_urls:
        raise HTTPException(
            status_code=400,
            detail=f"URLs não suportadas: {unsupported_urls}"
        )

    # Cria tasks
    task_ids = []
    for url in request.urls:
        task = process_and_publish.delay(url, request.schema_name)
        task_ids.append({
            "url": url,
            "task_id": task.id
        })

    return {
        "status": "batch_queued",
        "total": len(task_ids),
        "tasks": task_ids,
        "message": "Use /status/{task_id} para acompanhar cada task"
    }


@app.get("/publish/pending", tags=["WordPress"])
async def list_pending_publications(limit: int = 50):
    """
    Lista notícias que ainda não foram publicadas no WordPress

    Retorna notícias processadas com sucesso mas pendentes de publicação.
    """

    repo = MongoNewsRepository()
    pending = repo.find_pending_publish(limit=limit)

    return {
        "total": len(pending),
        "pending": [
            {
                "mongodb_id": p["_id"],
                "title": p.get("title", p.get("article", {}).get("title", "Sem título")),
                "url": p.get("url"),
                "created_at": p.get("created_at"),
                "publish_attempts": p.get("publish_attempts", 0),
                "publish_error": p.get("publish_error")
            }
            for p in pending
        ]
    }


@app.get("/publish/stats", tags=["WordPress"])
async def get_publish_statistics():
    """
    Retorna estatísticas de publicação

    - total: Total de notícias no MongoDB
    - published: Notícias publicadas no WordPress
    - pending: Notícias pendentes de publicação
    - with_errors: Notícias com erro de publicação
    """

    repo = MongoNewsRepository()
    stats = repo.get_publish_stats()

    return {
        "stats": stats,
        "message": "Use /publish/batch com publish_pending=true para publicar pendentes"
    }


@app.get("/wordpress/health", tags=["WordPress"])
async def wordpress_health():
    """
    Verifica se o WordPress está acessível e pronto para receber conteúdo
    Retorna diagnóstico completo:
    - wordpress_accessible: Se o WordPress está online
    - rest_api_working: Se a REST API está funcionando (permalinks configurados)
    - plugin_active: Se o plugin Content Receiver está ativado
    - ready: Se tudo está pronto para publicar
    """
    publisher = WordPressPublisherService()
    health = publisher.health_check()

    return {
        "status": "ready" if health["ready"] else "not_ready",
        "wordpress_url": publisher.wordpress_url,
        "webhook_url": publisher.webhook_url,
        "checks": {
            "wordpress_accessible": health["wordpress_accessible"],
            "rest_api_working": health["rest_api_working"],
            "plugin_active": health["plugin_active"]
        },
        "issues": health["issues"] if health["issues"] else None,
        "message": "WordPress está pronto para receber conteúdo" if health["ready"] else "Verifique os problemas listados em 'issues'"
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
