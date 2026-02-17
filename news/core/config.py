import os
from dotenv import load_dotenv

load_dotenv(override=False)


class Settings:
    """Configurações centralizadas da aplicação"""

    # App
    APP_NAME = "news-structured-feed"
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"

    # MongoDB
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    MONGODB_DB = os.getenv("MONGODB_DB", "news_feed_db")

    # Redis/Celery
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)

    # LLM
    LLM_API_URL = os.getenv("LM_API_URL", "http://localhost:1234/api/v1/chat")
    LLM_MODEL = os.getenv("LM_MODEL", "qwen/qwen3-coder-next")
    LLM_API_TOKEN = os.getenv("LM_API_TOKEN", "")

    # Paths
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    SCHEMAS_DIR = os.path.join(BASE_DIR, "schemas")
    LOGS_DIR = os.path.join(BASE_DIR, "logs")

    @classmethod
    def get_schema_path(cls, schema_name: str) -> str:
        """Retorna o caminho completo para um schema"""
        if not schema_name.endswith('.yaml'):
            schema_name = f"{schema_name}.yaml"
        return os.path.join(cls.SCHEMAS_DIR, schema_name)

    @classmethod
    def list_schemas(cls) -> list:
        """Lista todos os schemas disponíveis"""
        if not os.path.exists(cls.SCHEMAS_DIR):
            return []
        return [f.replace('.yaml', '') for f in os.listdir(cls.SCHEMAS_DIR) if f.endswith('.yaml')]


settings = Settings()
