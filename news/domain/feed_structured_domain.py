from typing import List, Optional
from pydantic import BaseModel, Field


class FeedItem(BaseModel):
    """
    FeedItem representa um item individual do feed de notícias, contendo título, link, descrição e data de publicação.
    """
    title: str
    link: str
    description: Optional[str] = None
    pub_date: Optional[str] = None


class StructuredFeedResponse(BaseModel):
    """
    StructuredFeedResponse é o modelo principal que representa a resposta estruturada do feed de notícias.
    """
    status: str
    feed_title: Optional[str] = None
    feed_link: Optional[str] = None
    feed_description: Optional[str] = None
    items: List[FeedItem] = Field(default_factory=list)
