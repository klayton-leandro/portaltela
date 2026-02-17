import sys
import os
from loguru import logger
from core.config import settings


def setup_logging():

    # Remove o handler padrão
    logger.remove()

    # Cria diretório de logs se não existir
    os.makedirs(settings.LOGS_DIR, exist_ok=True)

    # Formato personalizado
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    # Console handler
    logger.add(
        sys.stdout,
        format=log_format,
        level="DEBUG" if settings.DEBUG else "INFO",
        colorize=True,
    )

    # Arquivo de log geral
    logger.add(
        os.path.join(settings.LOGS_DIR, "app_{time:YYYY-MM-DD}.log"),
        format=log_format,
        level="DEBUG",
        rotation="00:00",  # Rotaciona à meia-noite
        retention="7 days",  # Mantém por 7 dias
        compression="zip",
        encoding="utf-8",
    )

    # Arquivo de log de erros
    logger.add(
        os.path.join(settings.LOGS_DIR, "errors_{time:YYYY-MM-DD}.log"),
        format=log_format,
        level="ERROR",
        rotation="00:00",
        retention="30 days",
        compression="zip",
        encoding="utf-8",
    )

    # Arquivo de log de tasks Celery
    logger.add(
        os.path.join(settings.LOGS_DIR, "tasks_{time:YYYY-MM-DD}.log"),
        format=log_format,
        level="INFO",
        rotation="00:00",
        retention="14 days",
        compression="zip",
        encoding="utf-8",
        filter=lambda record: "celery" in record["name"].lower(
        ) or "task" in record["message"].lower(),
    )

    logger.info(f"Logging configurado - Logs em: {settings.LOGS_DIR}")

    return logger


# Configura o logging ao importar
log = setup_logging()
