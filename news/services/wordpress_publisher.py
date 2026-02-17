"""
Serviço para publicar notícias no WordPress via webhook
Envia conteúdo processado para o endpoint REST do plugin content-receiver
"""

import os
import requests
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from dotenv import load_dotenv

try:
    from core.logging import log
except ImportError:
    from loguru import logger as log

load_dotenv(override=False)


@dataclass
class WordPressPublishResult:
    """Resultado da publicação no WordPress"""
    success: bool
    post_id: Optional[int] = None
    post_url: Optional[str] = None
    error: Optional[str] = None


class WordPressPublisherService:
    """
    Serviço para publicar notícias no WordPress via webhook

    Envia dados para o endpoint: /wp-json/content-receiver/v1/webhook
    """

    DEFAULT_TIMEOUT = 30

    def __init__(
        self,
        wordpress_url: str = None,
        api_key: str = None,
        default_status: str = "publish"
    ):
        """
        Inicializa o serviço

        Args:
            wordpress_url: URL base do WordPress (ex: http://localhost:8080)
            api_key: Chave de API configurada no plugin
            default_status: Status padrão dos posts (publish, draft, pending)
        """
        self.wordpress_url = wordpress_url or os.environ.get(
            "WORDPRESS_URL", "http://localhost:8080"
        )
        self.api_key = api_key or os.environ.get("WORDPRESS_API_KEY", "")
        self.default_status = default_status
        self.timeout = int(os.environ.get(
            "WORDPRESS_TIMEOUT", self.DEFAULT_TIMEOUT))

        # Endpoint do webhook
        self.webhook_url = f"{self.wordpress_url.rstrip('/')}/wp-json/content-receiver/v1/webhook"

    def publish(
        self,
        title: str,
        content: str,
        excerpt: str = None,
        categories: List[str] = None,
        tags: List[str] = None,
        featured_image: str = None,
        meta: Dict[str, Any] = None,
        status: str = None
    ) -> WordPressPublishResult:
        """
        Publica uma notícia no WordPress

        Args:
            title: Título do post
            content: Conteúdo HTML do post
            excerpt: Resumo/descrição (opcional)
            categories: Lista de categorias (opcional)
            tags: Lista de tags (opcional)
            featured_image: URL da imagem destacada (opcional)
            meta: Metadados customizados (opcional)
            status: Status do post (publish, draft, pending)

        Returns:
            WordPressPublishResult com resultado da operação
        """
        log.info(f"Publicando no WordPress: {title[:50]}...")

        # Prepara payload
        payload = {
            "title": title,
            "content": content,
            "status": status or self.default_status,
        }

        if excerpt:
            payload["excerpt"] = excerpt

        if categories:
            payload["categories"] = categories

        if tags:
            payload["tags"] = tags

        if featured_image:
            payload["featured_image"] = featured_image

        if meta:
            payload["meta"] = meta

        # Headers
        headers = {
            "Content-Type": "application/json",
        }

        if self.api_key:
            headers["X-API-Key"] = self.api_key

        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )

            # Verifica se a resposta é JSON
            content_type = response.headers.get("content-type", "")
            is_json = "application/json" in content_type

            # Se recebeu HTML ao invés de JSON, a REST API não está funcionando
            if not is_json and response.status_code == 200:
                log.error("WordPress retornou HTML ao invés de JSON. Verifique:")
                log.error(
                    "1. Se os permalinks estão configurados (não pode ser 'Padrão/Plain')")
                log.error("2. Se o plugin 'Content Receiver' está ativado")
                return WordPressPublishResult(
                    success=False,
                    error="REST API não está funcionando. Configure os permalinks no WordPress (Configurações > Links Permanentes) e ative o plugin."
                )

            if response.status_code == 201:
                result = response.json()
                log.success(
                    f"Post criado com sucesso: ID {result.get('post_id')}")
                return WordPressPublishResult(
                    success=True,
                    post_id=result.get("post_id"),
                    post_url=result.get("post_url")
                )

            # Erro na criação
            error_detail = response.json() if is_json else response.text[:500]
            log.error(
                f"Erro ao publicar: {response.status_code} - {error_detail}")

            return WordPressPublishResult(
                success=False,
                error=f"HTTP {response.status_code}: {error_detail}"
            )

        except requests.exceptions.ConnectionError:
            log.error(
                f"Não foi possível conectar ao WordPress: {self.wordpress_url}")
            return WordPressPublishResult(
                success=False,
                error=f"Conexão recusada: {self.wordpress_url}"
            )

        except requests.exceptions.Timeout:
            log.error(f"Timeout ao conectar ao WordPress após {self.timeout}s")
            return WordPressPublishResult(
                success=False,
                error=f"Timeout após {self.timeout}s"
            )

        except Exception as e:
            log.exception(f"Erro inesperado: {e}")
            return WordPressPublishResult(
                success=False,
                error=str(e)
            )

    def publish_from_processed_news(
        self,
        processed_data: Dict[str, Any],
        category_name: str = None
    ) -> WordPressPublishResult:
        """
        Publica uma notícia a partir dos dados processados pelo ProcessNewsUseCase

        Args:
            processed_data: Dicionário com o resultado do processamento
            category_name: Categoria adicional (opcional)

        Returns:
            WordPressPublishResult
        """
        article = processed_data.get("article", {})
        llm_processing = processed_data.get("llm_processing", {})

        # Extrai dados
        title = article.get("title", processed_data.get("title", ""))
        content = article.get("content", "")
        subtitle = article.get("subtitle", "")
        resumo = llm_processing.get("resumo", "")
        source = article.get("source", "")
        author = article.get("author", "")
        pub_date = article.get("pub_date", "")
        images = article.get("images", [])
        original_url = article.get("url", processed_data.get("url", ""))

        # Formata o conteúdo com resumo da IA
        formatted_content = self._format_content(
            content=content,
            subtitle=subtitle,
            resumo=resumo,
            source=source,
            original_url=original_url
        )

        # Prepara categorias
        categories = []
        if source:
            categories.append(source.upper())
        if category_name:
            categories.append(category_name)

        # Prepara tags baseadas na fonte
        tags = ["IA", "Automático"]
        if source:
            tags.append(source)

        # images é uma lista de dicts: [{"url": "...", "alt": "..."}]
        featured_image = None
        if images and len(images) > 0:
            first_image = images[0]
            if isinstance(first_image, dict):
                featured_image = first_image.get("url")
            elif isinstance(first_image, str):
                featured_image = first_image

        meta = {
            "fonte_original": source,
            "url_original": original_url,
            "autor_original": author,
            "data_publicacao_original": pub_date,
            "processado_por_ia": "true",
            "llm_status": llm_processing.get("status", "unknown")
        }

        return self.publish(
            title=title,
            content=formatted_content,
            excerpt=resumo or subtitle,
            categories=categories,
            tags=tags,
            featured_image=featured_image,
            meta=meta
        )

    def _format_content(
        self,
        content: str,
        subtitle: str = "",
        resumo: str = "",
        source: str = "",
        original_url: str = ""
    ) -> str:
        """
        Formata o conteúdo do post com estrutura HTML adequada

        Args:
            content: Conteúdo original
            subtitle: Subtítulo
            resumo: Resumo gerado pela IA
            source: Nome da fonte
            original_url: URL original da notícia

        Returns:
            Conteúdo HTML formatado
        """
        parts = []

        # Subtítulo como lead
        if subtitle:
            parts.append(f'<p class="lead"><strong>{subtitle}</strong></p>')

        # Resumo da IA em destaque
        if resumo:
            parts.append(f'''
<blockquote class="ia-summary">
    <p><em>📝 Resumo gerado por IA:</em></p>
    <p>{resumo}</p>
</blockquote>
''')

        # Conteúdo principal
        parts.append(content)

        # Créditos e fonte
        if source or original_url:
            credits = '<hr><p class="source-credits"><em>'
            if source:
                credits += f'Fonte: {source}'
            if original_url:
                credits += f' | <a href="{original_url}" target="_blank" rel="noopener">Ver notícia original</a>'
            credits += '</em></p>'
            parts.append(credits)

        return "\n\n".join(parts)

    def batch_publish(
        self,
        news_list: List[Dict[str, Any]],
        category_name: str = None,
        delay_between: float = 1.0
    ) -> Dict[str, Any]:
        """
        Publica múltiplas notícias em batch

        Args:
            news_list: Lista de dicionários com dados processados
            category_name: Categoria adicional para todos os posts
            delay_between: Delay em segundos entre publicações (evita sobrecarga)

        Returns:
            Dicionário com resultados do batch
        """
        import time

        results = {
            "total": len(news_list),
            "success": 0,
            "failed": 0,
            "published": [],
            "errors": []
        }

        log.info(f"Iniciando batch publish de {len(news_list)} notícias")

        for i, news_data in enumerate(news_list):
            try:
                url = news_data.get("url", f"item_{i}")
                log.info(f"[{i+1}/{len(news_list)}] Publicando: {url[:50]}...")

                result = self.publish_from_processed_news(
                    news_data, category_name)

                if result.success:
                    results["success"] += 1
                    results["published"].append({
                        "url": url,
                        "mongodb_id": news_data.get("mongodb_id"),
                        "post_id": result.post_id,
                        "post_url": result.post_url
                    })
                else:
                    results["failed"] += 1
                    results["errors"].append({
                        "url": url,
                        "mongodb_id": news_data.get("mongodb_id"),
                        "error": result.error
                    })

                # Delay entre publicações
                if i < len(news_list) - 1 and delay_between > 0:
                    time.sleep(delay_between)

            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "url": news_data.get("url", f"item_{i}"),
                    "error": str(e)
                })
                log.exception(f"Erro ao publicar item {i}: {e}")

        log.info(
            f"Batch concluído: {results['success']} sucesso, {results['failed']} falhas")
        return results

    def health_check(self) -> dict:
        """
        Verifica se o WordPress está acessível e configurado corretamente

        Returns:
            dict com status detalhado
        """
        result = {
            "wordpress_accessible": False,
            "rest_api_working": False,
            "plugin_active": False,
            "ready": False,
            "issues": []
        }

        try:
            # 1. Verifica se o WordPress está acessível
            response = requests.get(
                f"{self.wordpress_url}/wp-json/",
                timeout=5
            )

            if response.status_code != 200:
                result["issues"].append(
                    f"WordPress retornou status {response.status_code}")
                return result

            result["wordpress_accessible"] = True

            # 2. Verifica se a REST API está retornando JSON
            content_type = response.headers.get("content-type", "")
            if "application/json" not in content_type:
                result["issues"].append(
                    "REST API não está funcionando. Configure os permalinks (não pode ser 'Padrão/Plain')")
                return result

            result["rest_api_working"] = True

            # 3. Verifica se o endpoint do plugin existe
            try:
                data = response.json()
                namespaces = data.get("namespaces", [])
                if "content-receiver/v1" in namespaces:
                    result["plugin_active"] = True
                else:
                    result["issues"].append(
                        "Plugin 'Content Receiver' não está ativado")
            except Exception:
                result["issues"].append(
                    "Não foi possível verificar namespace do plugin")

            result["ready"] = result["wordpress_accessible"] and result["rest_api_working"] and result["plugin_active"]

            return result

        except requests.exceptions.ConnectionError:
            result["issues"].append(
                f"Não foi possível conectar ao WordPress em {self.wordpress_url}")
            return result
        except Exception as e:
            result["issues"].append(f"Erro: {str(e)}")
            return result
