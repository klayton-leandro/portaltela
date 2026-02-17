# ⚙️ Portal Tela - Backend (News Service)

Serviço de processamento de notícias com extração automatizada, processamento via LLM e publicação no WordPress.

## 📋 Índice

- [Visão Geral](#-visão-geral)
- [Arquitetura](#-arquitetura)
- [Decisões Técnicas](#-decisões-técnicas)
- [Pré-requisitos](#-pré-requisitos)
- [Instalação](#-instalação)
- [Variáveis de Ambiente](#-variáveis-de-ambiente)
- [Execução](#-execução)
- [API Endpoints](#-api-endpoints)
- [Celery Workers](#-celery-workers)
- [Schemas YAML](#-schemas-yaml)
- [Troubleshooting](#-troubleshooting)

---

## 🎯 Visão Geral

O backend é responsável por:

1. **Extrair** conteúdo de portais de notícias via web scraping
2. **Processar** textos usando LLM local (LM Studio) para gerar resumos
3. **Armazenar** notícias estruturadas no MongoDB
4. **Publicar** conteúdo no WordPress via webhook

### Stack Tecnológica

| Tecnologia | Versão | Descrição |
|------------|--------|-----------|
| Python | 3.11+ | Linguagem principal |
| FastAPI | 0.109+ | Framework REST API |
| Celery | 5.3+ | Processamento assíncrono |
| Redis | 7.x | Message broker |
| MongoDB | 7.x | Banco de dados |
| LM Studio | 0.2+ | LLM local |

---

## 🏗️ Arquitetura

### Diagrama Geral

```
┌────────────────────────────────────────────────────────────────────────────┐
│                           BACKEND - NEWS SERVICE                            │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐                 │
│  │   FastAPI   │─────▶│    Redis    │─────▶│   Celery    │                 │
│  │   :8000     │      │   Broker    │      │   Workers   │                 │
│  └─────────────┘      └─────────────┘      └──────┬──────┘                 │
│        │                                          │                        │
│        │ Health                           ┌───────┴───────┐                │
│        │ Check                            │               │                │
│        ▼                           ┌──────▼─────┐  ┌──────▼──────┐         │
│  ┌─────────────┐                   │  Scraper   │  │    LLM      │         │
│  │   Flower    │                   │  (G1, etc) │  │  (LM Studio)│         │
│  │   :5555     │                   └──────┬─────┘  └──────┬──────┘         │
│  └─────────────┘                          │               │                │
│                                           └───────┬───────┘                │
│                                                   ▼                        │
│                                           ┌─────────────┐                  │
│                                           │   MongoDB   │                  │
│                                           │   :27017    │                  │
│                                           └──────┬──────┘                  │
│                                                  │                         │
│                                                  ▼                         │
│                                          ┌─────────────┐                   │
│                                          │  WordPress  │                   │
│                                          │   Webhook   │                   │
│                                          └─────────────┘                   │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### Clean Architecture

```
┌────────────────────────────────────────────────────────────┐
│                    CLEAN ARCHITECTURE                       │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │                 DOMAIN (Núcleo)                        │ │
│  │                                                        │ │
│  │  ┌─────────────────┐    ┌─────────────────────────┐   │ │
│  │  │    Entities     │    │      Interfaces         │   │ │
│  │  │  - NewsArticle  │    │  - ScraperInterface     │   │ │
│  │  │  - LLMResult    │    │  - RepositoryInterface  │   │ │
│  │  │                 │    │  - LLMServiceInterface  │   │ │
│  │  └─────────────────┘    └─────────────────────────┘   │ │
│  │                                                        │ │
│  │  ┌─────────────────────────────────────────────────┐  │ │
│  │  │                  Use Cases                       │  │ │
│  │  │            ProcessNewsUseCase                    │  │ │
│  │  └─────────────────────────────────────────────────┘  │ │
│  │                                                        │ │
│  │  ┌─────────────────────────────────────────────────┐  │ │
│  │  │                  Factories                       │  │ │
│  │  │    UseCaseFactory  |  ScraperFactory            │  │ │
│  │  └─────────────────────────────────────────────────┘  │ │
│  └───────────────────────────────────────────────────────┘ │
│                            │                               │
│  ┌─────────────────────────┼─────────────────────────────┐ │
│  │              INFRASTRUCTURE                            │ │
│  │                                                        │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  │ │
│  │  │   Scrapers   │  │  Repository  │  │  Services   │  │ │
│  │  │  G1Scraper   │  │  MongoNews   │  │ LLMService  │  │ │
│  │  │  (+ outros)  │  │  Repository  │  │ WPPublisher │  │ │
│  │  └──────────────┘  └──────────────┘  └─────────────┘  │ │
│  │                                                        │ │
│  │  ┌─────────────────────────────────────────────────┐  │ │
│  │  │                 Workers (Celery)                 │  │ │
│  │  │   process_news_url | publish_to_wordpress        │  │ │
│  │  └─────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                  PRESENTATION (API)                     │ │
│  │              FastAPI REST Endpoints                     │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Decisões Técnicas

### 1. Clean Architecture + SOLID

| Princípio | Aplicação |
|-----------|-----------|
| **SRP** | Cada classe tem uma única responsabilidade |
| **OCP** | Novos scrapers sem alterar código existente |
| **LSP** | Scrapers intercambiáveis via interface |
| **ISP** | Interfaces específicas por funcionalidade |
| **DIP** | Domínio depende de abstrações, não implementações |

### 2. Celery para Processamento Assíncrono

- **Filas separadas**: `news` (processamento), `publish` (WordPress)
- **Retry automático**: Backoff exponencial em falhas
- **Workers escaláveis**: Múltiplos workers em paralelo
- **Monitoramento**: Flower dashboard em tempo real

### 3. LLM Local (LM Studio)

- **Privacidade**: Dados processados localmente
- **Sem custos**: Não depende de APIs pagas
- **Fallback**: Resumo básico se LLM indisponível
- **Modelos flexíveis**: Troca sem alterar código

### 4. Schema-Driven Scraping

- **Configuração YAML**: Seletores por fonte
- **Extensível**: Novas fontes sem código
- **Manutenível**: Ajustes rápidos de seletores

---

## 📋 Pré-requisitos

- Python 3.11+
- Docker e Docker Compose (recomendado)
- LM Studio com modelo carregado
- MongoDB e Redis (local ou Docker)

---

## 🛠️ Instalação

### Opção 1: Docker (Recomendado)

```bash
cd news

# Copiar configurações
cp .env.example .env

# Editar variáveis de ambiente
nano .env

# Subir todos os serviços
docker-compose up -d
```

### Opção 2: Local

```bash
cd news

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou: venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt

# Copiar configurações
cp .env.example .env

# Editar variáveis
nano .env
```

---

## 🔐 Variáveis de Ambiente

### Arquivo `.env`

```dotenv
# ═══════════════════════════════════════════════════════════
#                         Aplicação
# ═══════════════════════════════════════════════════════════
DEBUG=true

# ═══════════════════════════════════════════════════════════
#                         MongoDB
# ═══════════════════════════════════════════════════════════
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB=news_feed_db

# ═══════════════════════════════════════════════════════════
#                      Redis / Celery
# ═══════════════════════════════════════════════════════════
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# ═══════════════════════════════════════════════════════════
#                      LLM (LM Studio)
# ═══════════════════════════════════════════════════════════
LM_API_URL=http://localhost:1234/api/v1/chat
LM_MODEL=phi-3-mini-4k-instruct
LM_API_TOKEN=
LM_TIMEOUT=180
LM_MAX_RETRIES=2

# ═══════════════════════════════════════════════════════════
#                        WordPress
# ═══════════════════════════════════════════════════════════
WORDPRESS_URL=http://localhost:8080
WORDPRESS_API_KEY=sua_chave_secreta
WORDPRESS_TIMEOUT=30
```

### Tabela de Variáveis

| Variável | Obrigatória | Default | Descrição |
|----------|:-----------:|---------|-----------|
| `DEBUG` | ❌ | `false` | Modo debug |
| `MONGODB_URI` | ✅ | - | URI do MongoDB |
| `MONGODB_DB` | ✅ | - | Nome do banco |
| `REDIS_URL` | ✅ | - | URL do Redis |
| `CELERY_BROKER_URL` | ✅ | - | Broker Celery |
| `CELERY_RESULT_BACKEND` | ✅ | - | Backend resultados |
| `LM_API_URL` | ✅ | - | Endpoint LM Studio |
| `LM_MODEL` | ❌ | auto | Modelo LLM |
| `LM_API_TOKEN` | ❌ | - | Token auth |
| `LM_TIMEOUT` | ❌ | 180 | Timeout (segundos) |
| `LM_MAX_RETRIES` | ❌ | 2 | Retries |
| `WORDPRESS_URL` | ✅ | - | URL WordPress |
| `WORDPRESS_API_KEY` | ⚠️ | - | API Key plugin |
| `WORDPRESS_TIMEOUT` | ❌ | 30 | Timeout (segundos) |

---

## 🚀 Execução

### Docker Compose

```bash
# Iniciar todos os serviços
docker-compose up -d

# Ver logs
docker-compose logs -f

# Parar serviços
docker-compose down
```

**Serviços disponíveis:**
- API: `http://localhost:8000`
- Flower: `http://localhost:5555`
- MongoDB: `localhost:27017`
- Redis: `localhost:6380`

### Execução Local

**Terminal 1 - API:**
```bash
python run.py api
```

**Terminal 2 - Worker:**
```bash
python run.py worker
```

**Terminal 3 - Flower (opcional):**
```bash
python run.py flower
```

### Comandos Diretos

```bash
# API
uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload

# Worker (fila news)
celery -A workers.celery_app worker --loglevel=info --pool=solo -Q celery,news

# Worker (fila publish)
celery -A workers.celery_app worker --loglevel=info --pool=solo -Q publish

# Flower
celery -A workers.celery_app flower --port=5555
```

---

## 📡 API Endpoints

### Base URL: `http://localhost:8000`

### Health & Status

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/` | Status da API |
| `GET` | `/health` | Health check completo |
| `GET` | `/health/llm` | Status do LLM |

### Processamento

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `POST` | `/news/process` | Processa uma URL |
| `POST` | `/news/batch` | Processa múltiplas URLs |
| `GET` | `/task/{task_id}` | Status de uma task |

### Schemas e Fontes

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/schemas` | Lista schemas disponíveis |
| `GET` | `/sources` | Lista fontes suportadas |

### MongoDB

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/news/recent` | Notícias recentes |
| `GET` | `/news/{mongodb_id}` | Busca por ID |

### WordPress

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `POST` | `/wordpress/publish/{mongodb_id}` | Publica uma notícia |
| `POST` | `/wordpress/publish/batch` | Publica em lote |

### Exemplos

**Processar notícia:**
```bash
curl -X POST http://localhost:8000/news/process \
  -H "Content-Type: application/json" \
  -d '{"url": "https://g1.globo.com/...", "schema_name": "g1"}'
```

**Resposta:**
```json
{
  "task_id": "abc123-def456",
  "status": "queued",
  "message": "Task enviada para processamento"
}
```

**Verificar status:**
```bash
curl http://localhost:8000/task/abc123-def456
```

**Publicar no WordPress:**
```bash
curl -X POST http://localhost:8000/wordpress/publish/65abc123def456
```

---

## 👷 Celery Workers

### Filas

| Fila | Descrição | Worker |
|------|-----------|--------|
| `celery` | Fila padrão | celery-worker |
| `news` | Processamento de notícias | celery-worker |
| `publish` | Publicação WordPress | celery-worker-publish |

### Tasks Principais

| Task | Descrição |
|------|-----------|
| `process_news_url` | Processa uma URL de notícia |
| `process_news_batch` | Processa lote de URLs |
| `publish_to_wordpress` | Publica no WordPress |
| `health_check` | Verifica saúde do worker |

### Monitoramento (Flower)

Acesse `http://localhost:5555` para:
- Ver tasks em execução
- Histórico de processamento
- Status dos workers
- Métricas de filas

---

## 📄 Schemas YAML

### Localização

```
news/schemas/
└── g1.yaml
```

### Estrutura do Schema

```yaml
# Comportamento do LLM
comportamento:
  - role: system
    content: |
      Você resume notícias de forma concisa em até 3 frases.

# Padrões regex para limpeza
regex_patterns:
  - name: limpar_espacos_duplicados
    pattern: "\\s{2,}"
    replacement: " "
    
  - name: remover_leia_mais
    pattern: "LEIA TAMBÉM:.*$"
    flags: "i"
    replacement: ""

# Validações
validations:
  min_content_length: 100
  max_resumo_length: 500
  required_fields:
    - title
    - content

# Configuração da fonte
source_config:
  name: g1
  domains:
    - g1.globo.com
  selectors:
    title:
      - "h1.content-head__title"
      - "h1[itemprop='headline']"
    subtitle:
      - "h2.content-head__subtitle"
    content:
      - "article .content-text"
      - ".mc-article-body"
```

### Adicionando Nova Fonte

1. Crie `schemas/nova_fonte.yaml` com configurações
2. Crie `scraper/nova_fonte_scraper.py` implementando `ScraperInterface`
3. Registre no `ScraperFactory`

---

## 🐛 Troubleshooting

### LLM não responde

```bash
# Verificar se LM Studio está rodando
curl http://localhost:1234/api/v1/models

# Verificar health check
curl http://localhost:8000/health/llm
```

**Solução**: Inicie o LM Studio e carregue um modelo.

### Celery não processa tasks

```bash
# Verificar Redis
redis-cli ping

# Verificar logs do worker
docker-compose logs celery-worker
```

**Solução**: Verifique a URL do Redis no `.env`.

### MongoDB connection refused

```bash
# Verificar MongoDB
mongosh mongodb://localhost:27017

# Docker
docker-compose logs mongodb
```

**Solução**: Certifique-se que o MongoDB está rodando.

### WordPress retorna erro

```bash
# Testar conexão
curl http://localhost:8080/wp-json/content-receiver/v1/webhook \
  -H "Content-Type: application/json" \
  -d '{"title": "Teste", "content": "Conteúdo"}'
```

**Verificar**:
1. Plugin ativado
2. Permalinks configurados (não "Padrão")
3. API Key correta

---

## 📁 Estrutura de Arquivos

```
news/
├── api/
│   ├── __init__.py
│   └── app.py                  # FastAPI application
├── core/
│   ├── __init__.py
│   ├── config.py               # Configurações
│   └── logging.py              # Loguru setup
├── domain/
│   ├── entities/
│   │   ├── news_article.py     # Entidade notícia
│   │   └── llm_result.py       # Resultado LLM
│   ├── interfaces/
│   │   ├── scraper_interface.py
│   │   └── repository_interface.py
│   ├── usecases/
│   │   └── process_news_usecase.py
│   └── factories.py            # DI factories
├── infra/
│   ├── mongodb_infra.py        # Cliente MongoDB
│   └── mongo_news_repository.py
├── scraper/
│   ├── __init__.py
│   └── g1_scraper.py           # Scraper G1
├── services/
│   ├── llm_service.py          # Integração LLM
│   ├── llm_service_adapter.py  # Adapter
│   └── wordpress_publisher.py  # Publicador WP
├── workers/
│   ├── celery_app.py           # Config Celery
│   └── tasks.py                # Tasks
├── schemas/
│   └── g1.yaml                 # Schema G1
├── logs/                       # Arquivos de log
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── run.py                      # CLI de execução
├── .env.example
└── README.md
```

---

## 🔗 Links Úteis

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Celery Documentation](https://docs.celeryq.dev/)
- [LM Studio](https://lmstudio.ai/)
- [MongoDB Documentation](https://www.mongodb.com/docs/)
- [Redis Documentation](https://redis.io/docs/)

---

## 👥 Autor

**Klayton Leandro Matos de Paula**
