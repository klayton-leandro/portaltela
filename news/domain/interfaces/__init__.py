from domain.entities import NewsArticle, LLMResult
from .scraper_interface import ScraperInterface
from .repository_interface import NewsRepositoryInterface, LLMServiceInterface

__all__ = [
    'ScraperInterface',
    'NewsArticle',
    'NewsRepositoryInterface',
    'LLMServiceInterface',
    'LLMResult'
]
