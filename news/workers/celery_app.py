"""
Configuração do Celery para processamento assíncrono
"""
from celery import Celery
from core.config import settings

# Cria a instância do Celery
celery_app = Celery(
    "news_structured_feed",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["workers.tasks"]
)

# Configurações do Celery
celery_app.conf.update(
    # Serialização
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # Timezone
    timezone="America/Sao_Paulo",
    enable_utc=True,

    # Tasks
    task_track_started=True,
    task_time_limit=300,  # 5 minutos

    # Results
    result_expires=3600,  # Resultados expiram em 1 hora

    # Worker - Windows compatibility
    worker_prefetch_multiplier=1,
    worker_concurrency=1,  # Solo no Windows

    # Retry
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # Logging
    worker_hijack_root_logger=False,
)

# Configuração de rotas de tasks (opcional)
celery_app.conf.task_routes = {
    "workers.tasks.process_news_url": {"queue": "news"},
    "workers.tasks.process_news_batch": {"queue": "news"},
    "workers.tasks.publish_to_wordpress": {"queue": "publish"},
    "workers.tasks.publish_batch_to_wordpress": {"queue": "publish"},
    "workers.tasks.process_and_publish": {"queue": "news"},
}

# Configuração de rate limits (opcional)
celery_app.conf.task_annotations = {
    "workers.tasks.process_news_url": {
        "rate_limit": "10/m"  # 10 por minuto
    },
    "workers.tasks.publish_to_wordpress": {
        "rate_limit": "30/m"  # 30 por minuto - evita sobrecarga no WP
    },
    "workers.tasks.process_and_publish": {
        "rate_limit": "5/m"  # 5 por minuto - mais pesada
    },
}
