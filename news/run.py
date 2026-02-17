import sys
import os
import uvicorn
from core.logging import log
from workers.celery_app import celery_app
from core.logging import log
import subprocess
import sys
from core.logging import log


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_api():
    """Executa a API FastAPI"""

    log.info("Iniciando API FastAPI...")
    uvicorn.run(
        "api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


def run_worker():
    """Executa o worker Celery"""

    log.info("Iniciando Celery Worker...")
    celery_app.worker_main([
        'worker',
        '--loglevel=info',
        '--pool=solo',  # Windows compatibility
        '-Q', 'celery,news'
    ])


def run_flower():
    """Executa o Flower (monitor do Celery)"""

    log.info("Iniciando Flower na porta 5555...")
    log.info("Acesse: http://localhost:5555")

    try:
        subprocess.run([
            sys.executable, "-m", "celery",
            "-A", "workers.celery_app",
            "flower",
            "--port=5555"
        ], check=True)
    except FileNotFoundError:
        log.error("Flower não instalado. Execute: pip install flower")
        sys.exit(1)


def show_help():
    """Mostra ajuda"""
    print("""
News Structured Feed - Comandos disponíveis:

    python run.py api      - Inicia a API FastAPI (porta 8000)
    python run.py worker   - Inicia o Celery Worker
    python run.py flower   - Inicia o Flower (monitor Celery, porta 5555)
    
Pré-requisitos:
    - Redis rodando em localhost:6379
    - MongoDB rodando em localhost:27017
    - LLM API rodando em localhost:1234

Para iniciar todos os serviços, abra 2 terminais:
    Terminal 1: python run.py api
    Terminal 2: python run.py worker
    """)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        show_help()
        sys.exit(0)

    command = sys.argv[1].lower()

    if command == "api":
        run_api()
    elif command == "worker":
        run_worker()
    elif command == "flower":
        run_flower()
    else:
        print(f"Comando desconhecido: {command}")
        show_help()
        sys.exit(1)
