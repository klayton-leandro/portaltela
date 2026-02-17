import requests
import re
import yaml
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse

try:
    from core.logging import log
except ImportError:
    from loguru import logger as log

from core.config import settings
from domain.interfaces import ScraperInterface, NewsArticle


class G1Scraper(ScraperInterface):
    """
    Scraper para extrair notícias do portal G1
    Implementa ScraperInterface (Dependency Inversion Principle)
    Usa configurações do schema YAML para seletores e validações
    """

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
    }

    # Seletores padrão (fallback caso o schema não esteja disponível)
    DEFAULT_SELECTORS = {
        'title': ['h1.content-head__title', 'h1[itemprop="headline"]', 'h1.title', 'article h1', 'h1'],
        'subtitle': ['h2.content-head__subtitle', 'h2[itemprop="description"]', '.content-head__subtitle', 'article h2'],
        'content': ['article .content-text', '.mc-article-body', 'article .post-content', '.content-text__container', 'article p'],
        'author': ['.content-publication-data__from', '[itemprop="author"]', '.author', 'address.author'],
        'pub_date': ['.content-publication-data__updated time', '.content-publication-data__created time', 'time[itemprop="datePublished"]', '.date'],
        'images': ['article figure img', '.content-media__image img', 'article img[src]']
    }

    DEFAULT_DOMAINS = ['g1.globo.com', 'www.g1.globo.com']

    def __init__(self, schema_name: str = "g1"):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        self.schema_name = schema_name
        self.schema = self._load_schema(schema_name)
        self._init_from_schema()

    def _load_schema(self, schema_name: str) -> Optional[Dict[str, Any]]:
        """Carrega o schema YAML para configuração do scraper"""
        try:
            schema_path = settings.get_schema_path(schema_name)
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = yaml.safe_load(f)
            log.info(f"Schema '{schema_name}' carregado com sucesso")
            return schema
        except FileNotFoundError:
            log.warning(
                f"Schema '{schema_name}' não encontrado, usando configurações padrão")
            return None
        except Exception as e:
            log.error(f"Erro ao carregar schema '{schema_name}': {e}")
            return None

    def _init_from_schema(self):
        """Inicializa configurações a partir do schema"""
        if self.schema and 'source_config' in self.schema:
            source_config = self.schema['source_config']
            # Domínios suportados
            self.supported_domains = source_config.get(
                'domains', self.DEFAULT_DOMAINS)
            # Seletores CSS
            self.selectors = source_config.get(
                'selectors', self.DEFAULT_SELECTORS)
        else:
            self.supported_domains = self.DEFAULT_DOMAINS
            self.selectors = self.DEFAULT_SELECTORS

        # Regex patterns para limpeza de texto
        self.regex_patterns = []
        if self.schema and 'regex_patterns' in self.schema:
            self.regex_patterns = self.schema['regex_patterns']

        # Validações
        self.validations = {}
        if self.schema and 'validations' in self.schema:
            self.validations = self.schema['validations']

    @property
    def source_name(self) -> str:
        """Retorna o nome da fonte"""
        return "g1"

    def can_handle(self, url: str) -> bool:
        """
        Verifica se este scraper pode processar a URL

        Args:
            url: URL para verificar

        Returns:
            True se a URL é do G1
        """
        try:
            parsed = urlparse(url)
            return parsed.netloc in self.supported_domains
        except Exception:
            return False

    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Baixa e parseia a página HTML"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'lxml')
        except requests.RequestException as e:
            log.error(f"Erro ao acessar página: {e}")
            return None

    def _get_selectors(self, selector_type: str) -> List[str]:
        """Retorna os seletores para um tipo específico do schema ou fallback"""
        return self.selectors.get(selector_type, self.DEFAULT_SELECTORS.get(selector_type, []))

    def extract_title(self, soup: BeautifulSoup) -> str:
        """Extrai o título da notícia usando seletores do schema"""
        selectors = self._get_selectors('title')
        for selector in selectors:
            title = soup.select_one(selector)
            if title:
                return title.get_text(strip=True)
        return "Título não encontrado"

    def extract_subtitle(self, soup: BeautifulSoup) -> Optional[str]:
        """Extrai o subtítulo/resumo da notícia usando seletores do schema"""
        selectors = self._get_selectors('subtitle')
        for selector in selectors:
            subtitle = soup.select_one(selector)
            if subtitle:
                return subtitle.get_text(strip=True)
        return None

    def extract_content(self, soup: BeautifulSoup) -> str:
        """Extrai o conteúdo principal da notícia usando seletores do schema"""
        content_selectors = self._get_selectors('content')

        for selector in content_selectors:
            content_elements = soup.select(selector)
            if content_elements:
                paragraphs = []
                for element in content_elements:
                    # Pega todos os parágrafos dentro do elemento
                    if element.name == 'p':
                        text = element.get_text(strip=True)
                        if text:
                            paragraphs.append(text)
                    else:
                        for p in element.find_all('p'):
                            text = p.get_text(strip=True)
                            if text:
                                paragraphs.append(text)

                if paragraphs:
                    return '\n\n'.join(paragraphs)

        # Fallback: tenta pegar todo o texto do artigo
        article = soup.select_one('article')
        if article:
            return article.get_text(separator='\n', strip=True)

        return "Conteúdo não encontrado"

    def extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extrai o autor da notícia usando seletores do schema"""
        selectors = self._get_selectors('author')
        for selector in selectors:
            author = soup.select_one(selector)
            if author:
                text = author.get_text(strip=True)
                # Remove prefixos comuns
                text = text.replace('Por ', '').replace('por ', '')
                return text
        return None

    def extract_pub_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extrai a data de publicação usando seletores do schema"""
        # Tenta encontrar datetime no atributo
        time_element = soup.select_one('time[datetime]')
        if time_element:
            return time_element.get('datetime')

        selectors = self._get_selectors('pub_date')
        for selector in selectors:
            date_elem = soup.select_one(selector)
            if date_elem:
                return date_elem.get_text(strip=True)
        return None

    def extract_images(self, soup: BeautifulSoup) -> list:
        """Extrai URLs das imagens da notícia usando seletores do schema"""
        images = []
        img_selectors = self._get_selectors('images')

        for selector in img_selectors:
            for img in soup.select(selector):
                src = img.get('src') or img.get('data-src')
                if src and not src.startswith('data:'):
                    images.append({
                        'url': src,
                        'alt': img.get('alt', '')
                    })

        return images

    def _apply_regex_patterns(self, text: str) -> str:
        """Aplica os padrões regex do schema ao texto"""
        for pattern_config in self.regex_patterns:
            try:
                pattern = pattern_config.get('pattern', '')
                replacement = pattern_config.get('replacement', '')
                flags_str = pattern_config.get('flags', '')

                # Converte flags string para flags do re
                flags = 0
                if 'i' in flags_str.lower():
                    flags |= re.IGNORECASE
                if 'm' in flags_str.lower():
                    flags |= re.MULTILINE

                text = re.sub(pattern, replacement, text, flags=flags)
            except Exception as e:
                log.warning(
                    f"Erro ao aplicar regex pattern '{pattern_config.get('name', 'unknown')}': {e}")

        return text

    def clean_text(self, text: str) -> str:
        """Limpa o texto usando regex_patterns do schema e regras padrão"""
        # Aplica padrões do schema primeiro
        text = self._apply_regex_patterns(text)

        # Remove múltiplos espaços (fallback padrão)
        text = re.sub(r'\s+', ' ', text)
        # Remove espaços no início e fim
        text = text.strip()
        return text

    def _validate_content(self, title: str, content: str) -> bool:
        """Valida o conteúdo extraído conforme regras do schema"""
        if not self.validations:
            return True

        # Verifica campos obrigatórios
        required_fields = self.validations.get('required_fields', [])
        if 'title' in required_fields and (not title or title == "Título não encontrado"):
            log.warning("Validação falhou: título obrigatório não encontrado")
            return False
        if 'content' in required_fields and (not content or content == "Conteúdo não encontrado"):
            log.warning(
                "Validação falhou: conteúdo obrigatório não encontrado")
            return False

        # Verifica tamanho mínimo do conteúdo
        min_length = self.validations.get('min_content_length', 0)
        if len(content) < min_length:
            log.warning(
                f"Validação falhou: conteúdo com {len(content)} chars, mínimo {min_length}")
            return False

        return True

    def scrape(self, url: str) -> Optional[NewsArticle]:
        """Extrai todos os dados de uma notícia usando configurações do schema"""
        log.info(f"Acessando: {url} (schema: {self.schema_name})")
        soup = self.fetch_page(url)

        if not soup:
            return None

        title = self.extract_title(soup)
        subtitle = self.extract_subtitle(soup)
        content = self.extract_content(soup)
        author = self.extract_author(soup)
        pub_date = self.extract_pub_date(soup)
        images = self.extract_images(soup)

        # Limpa os textos usando regex patterns do schema
        content = self.clean_text(content)

        # Valida conforme regras do schema
        if not self._validate_content(title, content):
            log.warning(
                f"Conteúdo não passou na validação do schema '{self.schema_name}'")

        return NewsArticle(
            title=title,
            subtitle=subtitle,
            content=content,
            author=author,
            pub_date=pub_date,
            url=url,
            images=images,
            source=self.source_name
        )
