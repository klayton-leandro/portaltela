# 📰 Portal Tela - Sistema de Automação de Notícias

Sistema completo de extração, processamento com IA e publicação automatizada de notícias, composto por um **backend** de processamento (Python/FastAPI) e um **frontend** WordPress.

---

## 📋 Índice

- [Visão Geral](#-visão-geral)
- [Arquitetura da Solução](#-arquitetura-da-solução)
- [Componentes](#-componentes)
- [Quick Start](#-quick-start)
- [Documentação Detalhada](#-documentação-detalhada)
- [Variáveis de Ambiente](#-variáveis-de-ambiente)
- [Fluxo de Processamento](#-fluxo-de-processamento)
- [Decisões Técnicas](#-decisões-técnicas)
- [Estrutura do Projeto](#-estrutura-do-projeto)

---

## 🎯 Visão Geral

O **Portal Tela** é uma solução end-to-end para automação de conteúdo jornalístico:

| Etapa | Descrição | Tecnologia |
|-------|-----------|------------|
| **1. Extração** | Web scraping de portais de notícias | BeautifulSoup + Schemas YAML |
| **2. Processamento** | Geração de resumos via IA | LM Studio (LLM Local) |
| **3. Armazenamento** | Persistência estruturada | MongoDB |
| **4. Publicação** | Posts automáticos no CMS | WordPress REST API |
| **5. Exibição** | Portal de notícias responsivo | Tema WordPress + Bootstrap |

---

## 🏗️ Arquitetura da Solução

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                            PORTAL TELA - ARQUITETURA                                 │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌────────────────────────────────────┐    ┌────────────────────────────────────┐   │
│  │           BACKEND (news/)          │    │        FRONTEND (frontend/)        │   │
│  │                                    │    │                                    │   │
│  │  ┌──────────┐    ┌──────────────┐  │    │  ┌─────────────┐   ┌────────────┐  │   │
│  │  │ FastAPI  │───▶│    Celery    │  │    │  │    Nginx    │──▶│  PHP-FPM   │  │   │
│  │  │  :8000   │    │   Workers    │  │    │  │    :8080    │   │  WordPress │  │   │
│  │  └──────────┘    └──────┬───────┘  │    │  └─────────────┘   └─────┬──────┘  │   │
│  │       │                 │          │    │                          │         │   │
│  │       │          ┌──────┴──────┐   │    │                   ┌──────┴──────┐  │   │
│  │       │          │             │   │    │                   │             │  │   │
│  │  ┌────▼────┐  ┌──▼───┐  ┌──────▼─┐│    │            ┌──────▼──────┐      │  │   │
│  │  │  Redis  │  │Scraper│  │  LLM   ││    │            │   MySQL     │      │  │   │
│  │  │ Broker  │  │ (G1)  │  │LMStudio││    │            │  Database   │      │  │   │
│  │  └─────────┘  └───────┘  └────────┘│    │            └─────────────┘      │  │   │
│  │       │                      │     │    │                                  │  │   │
│  │       │              ┌───────┴──┐  │    │  ┌───────────────────────────┐   │  │   │
│  │  ┌────▼────┐         │ MongoDB  │  │    │  │    Plugin: Content        │   │  │   │
│  │  │ Flower  │         │          │──┼────┼─▶│    Receiver (Webhook)     │   │  │   │
│  │  │  :5555  │         └──────────┘  │    │  └───────────────────────────┘   │  │   │
│  │  └─────────┘                       │    │                                  │  │   │
│  │                                    │    │  ┌───────────────────────────┐   │  │   │
│  └────────────────────────────────────┘    │  │    Theme: Portal Tela     │   │  │   │
│                                            │  │    (Bootstrap 5 + Vite)   │   │  │   │
│                                            │  └───────────────────────────┘   │  │   │
│                                            │                                  │  │   │
│                                            └────────────────────────────────────┘   │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📦 Componentes

| Componente | Diretório | Descrição | Documentação |
|------------|-----------|-----------|--------------|
| **Backend** | `news/` | Serviço de processamento de notícias | [📖 README](news/README.md) |
| **Frontend** | `frontend/` | WordPress + Tema + Plugin | [📖 README](frontend/README.md) |

### Stack Tecnológica

| Camada | Tecnologia | Versão |
|--------|------------|--------|
| **Backend API** | FastAPI | 0.109+ |
| **Queue** | Celery + Redis | 5.3+ / 7.x |
| **Database** | MongoDB | 7.x |
| **LLM** | LM Studio | 0.2+ |
| **CMS** | WordPress | 6.x |
| **Web Server** | Nginx | latest |
| **Frontend Build** | Vite + Bootstrap | 5.x |

---

## 🚀 Quick Start

### Pré-requisitos

- Docker e Docker Compose
- LM Studio com modelo carregado
- Node.js 18+ (para build do tema)

### 1. Clone o Repositório

```bash
git clone <repository-url>
cd portaltela
```

### 2. Inicie o Backend

```bash
cd news
cp .env.example .env
# Configure as variáveis de ambiente no .env
docker-compose up -d
```

### 3. Inicie o Frontend

```bash
cd ../frontend
docker-compose up -d
```

### 4. Configure o WordPress

1. Acesse `http://localhost:8080` e complete a instalação
2. Ative o plugin **Content Receiver**
3. Ative o tema **Portal Tela**
4. Configure os **permalinks** (não pode ser "Padrão")

### 5. Verifique os Serviços

| Serviço | URL |
|---------|-----|
| API Backend | http://localhost:8000 |
| Flower (Monitor) | http://localhost:5555 |
| WordPress | http://localhost:8080 |
| LM Studio | http://localhost:1234 |

---

## 📚 Documentação Detalhada

### Backend (News Service)

Documentação completa do serviço de processamento:

👉 [**news/README.md**](news/README.md)

Inclui:
- Arquitetura Clean Architecture
- Configuração de variáveis de ambiente
- API Endpoints
- Celery Workers
- Schemas YAML
- Troubleshooting

### Frontend (WordPress)

Documentação completa do WordPress:

👉 [**frontend/README.md**](frontend/README.md)

Inclui:
- Plugin Content Receiver (webhook)
- Tema Portal Tela (Bootstrap 5)
- Docker configuration
- Customização

---

## 🔐 Variáveis de Ambiente

### Backend (`news/.env`)

```dotenv
# MongoDB
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB=news_feed_db

# Redis/Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# LLM (LM Studio)
LM_API_URL=http://localhost:1234/api/v1/chat
LM_MODEL=phi-3-mini-4k-instruct
LM_TIMEOUT=180

# WordPress
WORDPRESS_URL=http://localhost:8080
WORDPRESS_API_KEY=sua_chave_secreta
```

### Frontend (`frontend/docker-compose.yml`)

```yaml
environment:
  WORDPRESS_DB_HOST: db
  WORDPRESS_DB_USER: wpuser
  WORDPRESS_DB_PASSWORD: wppass
  WORDPRESS_DB_NAME: wordpress
```

> Veja documentação completa de cada componente nos READMEs específicos.

---

## 🔄 Fluxo de Processamento

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FLUXO COMPLETO DO SISTEMA                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────┐      ┌─────────┐      ┌─────────┐      ┌─────────────────────┐ │
│  │   URL   │─────▶│ Scraper │─────▶│   LLM   │─────▶│      MongoDB        │ │
│  │ Notícia │      │  (G1)   │      │ Resumo  │      │ Notícia Estruturada │ │
│  └─────────┘      └─────────┘      └─────────┘      └──────────┬──────────┘ │
│                                                                 │            │
│                                                                 ▼            │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                              WordPress                                   ││
│  │  ┌────────────────┐    ┌────────────────┐    ┌────────────────────────┐ ││
│  │  │ Content        │───▶│   Post         │───▶│   Portal Tela          │ ││
│  │  │ Receiver       │    │   Criado       │    │   (Tema Bootstrap)     │ ││
│  │  │ (Webhook)      │    │                │    │                        │ ││
│  │  └────────────────┘    └────────────────┘    └────────────────────────┘ ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Decisões Técnicas

| Decisão | Justificativa |
|---------|---------------|
| **Clean Architecture** | Separação de responsabilidades, testabilidade, manutenibilidade |
| **Celery + Redis** | Processamento assíncrono escalável com retry automático |
| **LLM Local** | Privacidade dos dados, sem custos de API externa |
| **Schema YAML** | Configuração de scrapers sem alterar código |
| **WordPress REST** | CMS robusto com ecossistema maduro |
| **Bootstrap 5** | UI responsiva com componentes prontos |

---

## 📁 Estrutura do Projeto

```
portaltela/
├── README.md                    # Este arquivo (visão geral)
│
├── news/                        # BACKEND - Serviço de processamento
│   ├── README.md               # Documentação do backend
│   ├── api/                    # FastAPI REST
│   ├── domain/                 # Entidades, interfaces, use cases
│   ├── infra/                  # MongoDB, infraestrutura
│   ├── scraper/                # Web scrapers
│   ├── services/               # LLM, WordPress publisher
│   ├── workers/                # Celery tasks
│   ├── schemas/                # Configurações YAML
│   ├── docker-compose.yml
│   └── requirements.txt
│
└── frontend/                    # FRONTEND - WordPress
    ├── README.md               # Documentação do frontend
    ├── wp-content/
    │   ├── plugins/
    │   │   └── content-receiver/   # Plugin webhook
    │   └── themes/
    │       └── portal-tela/        # Tema customizado
    ├── docker-compose.yml
    └── nginx/
```

---

## 🐛 Troubleshooting Rápido

| Problema | Solução |
|----------|---------|
| LLM não responde | Verifique se LM Studio está rodando com modelo carregado |
| WordPress retorna HTML | Configure permalinks (não "Padrão") |
| Celery não processa | Verifique se Redis está rodando |
| MongoDB offline | Verifique container: `docker-compose logs mongodb` |

> Veja troubleshooting detalhado nos READMEs específicos.

---

## 👥 Autor

**Klayton Leandro Matos de Paula**

---

## 📝 Licença

Este projeto está sob a licença MIT.

---

## 🔗 Links Úteis

- [FastAPI](https://fastapi.tiangolo.com/)
- [Celery](https://docs.celeryq.dev/)
- [LM Studio](https://lmstudio.ai/)
- [WordPress REST API](https://developer.wordpress.org/rest-api/)
- [MongoDB](https://www.mongodb.com/docs/)
- [Bootstrap 5](https://getbootstrap.com/docs/5.3/)

