from dataclasses import dataclass
from typing import Optional, List


@dataclass
class NewsArticle:
    """Entidade que representa uma notícia extraída"""
    title: str
    subtitle: Optional[str]
    content: str
    author: Optional[str]
    pub_date: Optional[str]
    url: str
    images: List[str]
    source: str = ""

    def __post_init__(self):
        """Validações após inicialização"""
        if not self.title:
            raise ValueError("Título é obrigatório")
        if not self.url:
            raise ValueError("URL é obrigatória")
        if self.images is None:
            self.images = []
