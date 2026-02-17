# 🌐 Portal Tela - Frontend (WordPress)

Frontend do Portal Tela construído com WordPress, tema customizado e plugin para recebimento de conteúdo via webhook.

## 📋 Índice

- [Visão Geral](#-visão-geral)
- [Arquitetura](#-arquitetura)
- [Pré-requisitos](#-pré-requisitos)
- [Instalação](#-instalação)
- [Plugin Content Receiver](#-plugin-content-receiver)
- [Tema Portal Tela](#-tema-portal-tela)
- [Docker](#-docker)
- [Configurações](#-configurações)

---

## 🎯 Visão Geral

O frontend é responsável por:

- **Exibir** notícias processadas pelo backend
- **Receber** novos posts via webhook REST API
- **Apresentar** conteúdo de forma responsiva e moderna

### Stack Tecnológica

| Tecnologia | Versão | Descrição |
|------------|--------|-----------|
| WordPress | 6.x | CMS principal |
| PHP | 8.2 | Runtime |
| MySQL | 8.0 | Banco de dados |
| Nginx | latest | Servidor web |
| Bootstrap | 5.3 | Framework CSS |
| Vite | 5.x | Build tool |

---

## 🏗️ Arquitetura

```
┌────────────────────────────────────────────────────────────────┐
│                     FRONTEND WORDPRESS                          │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────────┐   │
│  │   Nginx     │────▶│  PHP-FPM    │────▶│    MySQL        │   │
│  │   :8080     │     │  WordPress  │     │    Database     │   │
│  └─────────────┘     └──────┬──────┘     └─────────────────┘   │
│                             │                                   │
│                    ┌────────┴────────┐                         │
│                    │                 │                         │
│              ┌─────▼─────┐    ┌──────▼──────┐                  │
│              │   Theme   │    │   Plugin    │                  │
│              │  Portal   │    │  Content    │                  │
│              │   Tela    │    │  Receiver   │                  │
│              └───────────┘    └─────────────┘                  │
│                                     │                          │
│                                     ▼                          │
│                           REST API Webhook                     │
│                     /wp-json/content-receiver/v1/webhook       │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## 📋 Pré-requisitos

- Docker e Docker Compose
- Node.js 18+ (para build do tema)
- npm ou yarn

---

## 🛠️ Instalação

### 1. Iniciar os Containers

```bash
cd frontend

# Subir os serviços
docker-compose up -d

# Verificar status
docker-compose ps
```

### 2. Configurar WordPress

1. Acesse `http://localhost:8080`
2. Complete o wizard de instalação:
   - Idioma: Português do Brasil
   - Título do site: Portal Tela
   - Usuário: admin
   - Senha: (escolha uma senha segura)
   - Email: seu@email.com

### 3. Configurar Permalinks (OBRIGATÓRIO)

> ⚠️ **IMPORTANTE**: A REST API não funciona com permalinks "Padrão"

1. Acesse **Configurações > Links Permanentes**
2. Escolha **"Nome do post"** ou qualquer opção exceto "Padrão"
3. Clique em **Salvar alterações**

### 4. Ativar Plugin e Tema

```bash
# Via WP-CLI (dentro do container)
docker-compose exec php wp plugin activate content-receiver
docker-compose exec php wp theme activate portal-tela
```

Ou via painel admin:
1. **Plugins > Plugins Instalados** → Ativar "Content Receiver"
2. **Aparência > Temas** → Ativar "Portal Tela News Theme"

---

## 🔌 Plugin Content Receiver

### Descrição

O plugin **Content Receiver** expõe um endpoint REST API que recebe notícias do backend e cria posts automaticamente.

### Endpoint

```
POST /wp-json/content-receiver/v1/webhook
```

### Headers

| Header | Descrição |
|--------|-----------|
| `Content-Type` | `application/json` |
| `X-API-Key` | Chave de autenticação (se configurada) |

### Payload

```json
{
  "title": "Título da Notícia",
  "content": "<p>Conteúdo HTML da notícia...</p>",
  "excerpt": "Resumo opcional da notícia",
  "categories": ["Política", "Brasil"],
  "tags": ["eleições", "2026"],
  "featured_image": "https://url-da-imagem.jpg",
  "status": "publish",
  "meta": {
    "source_url": "https://fonte-original.com/noticia",
    "processed_at": "2026-02-17T10:30:00Z"
  }
}
```

### Campos Suportados

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `title` | string | ✅ | Título do post |
| `content` | string | ✅ | Conteúdo HTML |
| `excerpt` | string | ❌ | Resumo/descrição |
| `categories` | array | ❌ | Nomes ou IDs de categorias |
| `tags` | array | ❌ | Lista de tags |
| `featured_image` | string | ❌ | URL da imagem destacada |
| `status` | string | ❌ | `publish`, `draft`, `pending` |
| `post_type` | string | ❌ | Tipo de post (default: `post`) |
| `author_id` | int | ❌ | ID do autor (default: 1) |
| `date` | string | ❌ | Data de publicação |
| `slug` | string | ❌ | URL slug do post |
| `meta` | object | ❌ | Campos personalizados |

### Resposta de Sucesso

```json
{
  "success": true,
  "post_id": 123,
  "post_url": "http://localhost:8080/noticia-titulo/",
  "message": "Post criado com sucesso"
}
```

### Configuração da API Key

1. Acesse **Configurações > Content Receiver**
2. Defina uma API Key segura
3. Configure a mesma key no backend (`WORDPRESS_API_KEY`)

### Exemplo de Uso

```bash
curl -X POST http://localhost:8080/wp-json/content-receiver/v1/webhook \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sua_chave_secreta" \
  -d '{
    "title": "Título da Notícia",
    "content": "<p>Conteúdo da notícia...</p>",
    "categories": ["Tecnologia"],
    "status": "publish"
  }'
```

---

## 🎨 Tema Portal Tela

### Descrição

Tema WordPress moderno e responsivo construído com Bootstrap 5 e otimizado para portais de notícias.

### Características

- ✅ Design responsivo (mobile-first)
- ✅ Bootstrap 5.3 integrado
- ✅ Bootstrap Icons
- ✅ Build com Vite (SASS)
- ✅ Menus customizáveis
- ✅ Suporte a imagem destacada
- ✅ Tempo de leitura estimado
- ✅ Navegação por categorias

### Estrutura do Tema

```
portal-tela/
├── assets/              # Arquivos fonte (SASS)
│   └── scss/
│       └── main.scss
├── dist/                # Build compilado
│   ├── main.css
│   └── app.js
├── functions.php        # Funções do tema
├── header.php           # Template header
├── footer.php           # Template footer
├── index.php            # Home/archive
├── single.php           # Post individual
├── archive.php          # Arquivos/categorias
├── style.css            # Metadata do tema
├── package.json         # Dependências Node
└── vite.config.js       # Configuração Vite
```

### Instalação de Dependências

```bash
cd wp-content/themes/portal-tela

# Instalar dependências
npm install

# Build de produção
npm run build

# Desenvolvimento (watch mode)
npm run dev
```

### Customização do SASS

Edite `assets/scss/main.scss` para personalizar estilos:

```scss
// Importar Bootstrap
@import "bootstrap/scss/bootstrap";

// Variáveis customizadas
$primary: #0d6efd;
$font-family-base: 'Inter', sans-serif;

// Seus estilos customizados
.custom-class {
  // ...
}
```

### Menus

O tema suporta dois menus:
- **Menu Principal**: Navegação do header
- **Menu Rodapé**: Links do footer

Configure em **Aparência > Menus**.

---

## 🐳 Docker

### Serviços

| Serviço | Imagem | Porta | Descrição |
|---------|--------|-------|-----------|
| nginx | nginx:latest | 8080 | Servidor web |
| php | wordpress:php8.2-fpm | - | PHP-FPM + WordPress |
| db | mysql:8.0 | - | Banco de dados |

### docker-compose.yml

```yaml
services:
  nginx:
    image: nginx:latest
    ports:
      - "8080:80"
    volumes:
      - ./:/var/www/html
      - ./nginx/default.conf:/etc/nginx/conf.d/default.conf

  php:
    image: wordpress:php8.2-fpm
    volumes:
      - ./:/var/www/html
    environment:
      WORDPRESS_DB_HOST: db
      WORDPRESS_DB_USER: wpuser
      WORDPRESS_DB_PASSWORD: wppass
      WORDPRESS_DB_NAME: wordpress

  db:
    image: mysql:8.0
    environment:
      MYSQL_DATABASE: wordpress
      MYSQL_USER: wpuser
      MYSQL_PASSWORD: wppass
      MYSQL_ROOT_PASSWORD: rootpass
    volumes:
      - dbdata:/var/lib/mysql

volumes:
  dbdata:
```

### Comandos Úteis

```bash
# Iniciar serviços
docker-compose up -d

# Parar serviços
docker-compose down

# Ver logs
docker-compose logs -f

# Logs de um serviço específico
docker-compose logs -f php

# Acessar shell do container PHP
docker-compose exec php bash

# Reiniciar serviço
docker-compose restart nginx
```

---

## ⚙️ Configurações

### Nginx (nginx/default.conf)

```nginx
server {
    listen 80;
    server_name localhost;
    root /var/www/html;
    index index.php;

    location / {
        try_files $uri $uri/ /index.php?$args;
    }

    location ~ \.php$ {
        fastcgi_pass php:9000;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        include fastcgi_params;
    }
}
```

### wp-config.php

Variáveis importantes:

```php
// Debug mode (desenvolvimento)
define('WP_DEBUG', true);
define('WP_DEBUG_LOG', true);

// URLs
define('WP_HOME', 'http://localhost:8080');
define('WP_SITEURL', 'http://localhost:8080');

// Uploads
define('UPLOADS', 'wp-content/uploads');
```

---

## 🔧 Troubleshooting

### REST API retorna HTML ao invés de JSON

**Causa**: Permalinks configurados como "Padrão"

**Solução**:
1. Acesse **Configurações > Links Permanentes**
2. Selecione qualquer opção exceto "Padrão"
3. Salve

### Erro 404 no webhook

**Causa**: Plugin não ativado ou rewrite rules desatualizadas

**Solução**:
```bash
# Dentro do container
docker-compose exec php wp rewrite flush
```

### Imagem destacada não aparece

**Causa**: URL da imagem inacessível ou erro no download

**Verificar**:
1. URL da imagem é pública e acessível
2. Logs: `docker-compose logs php | grep featured_image`

### Permissões de arquivo

```bash
# Corrigir permissões
docker-compose exec php chown -R www-data:www-data /var/www/html/wp-content
docker-compose exec php chmod -R 755 /var/www/html/wp-content
```

---

## 📁 Estrutura de Arquivos

```
frontend/
├── docker-compose.yml      # Orquestração Docker
├── nginx/
│   └── default.conf        # Configuração Nginx
├── wp-admin/               # Core WordPress (admin)
├── wp-includes/            # Core WordPress (includes)
├── wp-content/
│   ├── plugins/
│   │   └── content-receiver/
│   │       └── content-receiver.php   # Plugin webhook
│   └── themes/
│       └── portal-tela/               # Tema customizado
│           ├── assets/                # SASS source
│           ├── dist/                  # CSS/JS compilado
│           ├── functions.php
│           ├── header.php
│           ├── footer.php
│           ├── index.php
│           ├── single.php
│           ├── archive.php
│           ├── style.css
│           ├── package.json
│           └── vite.config.js
├── wp-config.php           # Configurações WordPress
├── index.php               # Entry point
└── ...                     # Outros arquivos WP core
```

---

## 🔗 Links Úteis

- [WordPress Developer Resources](https://developer.wordpress.org/)
- [WordPress REST API Handbook](https://developer.wordpress.org/rest-api/)
- [Bootstrap 5 Documentation](https://getbootstrap.com/docs/5.3/)
- [Vite Documentation](https://vitejs.dev/)

---

## 👥 Autor

**Klayton Leandro Matos de Paula**
