
import sys
import os
from services.llm_service import LLMService, LLMResponse
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@dataclass
class NewsExtraction:
    """Resultado da extração de informações de uma notícia"""
    titulo: str
    subtitulo: str
    resumo: str
    status: str
    conteudo_original: str

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return asdict(self)


class LLMInterface:
    """Interface de alto nível para processamento de notícias com LLM"""

    def __init__(self, llm_service: LLMService = None):
        """
        Inicializa a interface com o serviço de LLM

        Args:
            llm_service: Instância do LLMService. Se não fornecido, cria uma nova.
        """
        self.llm_service = llm_service or LLMService()

    def extract_information(self, news_content: str, title: str = "", subtitle: str = "") -> Dict[str, Any]:
        """
        Extrai informações relevantes do conteúdo da notícia usando o LLM

        Args:
            news_content: Conteúdo bruto da notícia
            title: Título da notícia
            subtitle: Subtítulo da notícia

        Returns:
            Dicionário com as informações extraídas
        """
        # Processa o conteúdo usando o serviço de LLM
        response = self.llm_service.process_content(
            content=news_content,
            title=title,
            subtitle=subtitle
        )

        # Monta o resultado da extração
        extraction = NewsExtraction(
            titulo=title,
            subtitulo=subtitle,
            resumo=response.resumo,
            status=response.status,
            conteudo_original=news_content
        )

        return extraction.to_dict()

    def process_news(self, news_content: str, title: str = "", subtitle: str = "") -> LLMResponse:
        """
        Processa uma notícia e retorna a resposta da LLM diretamente

        Args:
            news_content: Conteúdo bruto da notícia
            title: Título da notícia
            subtitle: Subtítulo da notícia

        Returns:
            LLMResponse com resumo, texto limpo e status
        """
        return self.llm_service.process_content(
            content=news_content,
            title=title,
            subtitle=subtitle
        )

    def get_schema(self) -> Optional[Dict[str, Any]]:
        """Retorna o schema carregado no serviço"""
        return self.llm_service.schema

    def get_system_prompt(self) -> Optional[str]:
        """Retorna o prompt do sistema definido no schema"""
        return self.llm_service._get_system_prompt()

    def apply_regex_patterns(self, text: str) -> Dict[str, str]:
        """
        Aplica os padrões regex definidos no schema ao texto

        Args:
            text: Texto para aplicar os padrões

        Returns:
            Dicionário com os resultados dos grupos nomeados
        """
        return self.llm_service._apply_regex_patterns(text)

    def is_llm_available(self) -> bool:
        """
        Verifica se a LLM está disponível para processamento

        Returns:
            True se a LLM respondeu com sucesso, False caso contrário
        """
        try:
            response = self.llm_service.process_content(
                content="teste de conexão",
                title="Teste",
                subtitle=""
            )
            return response.status == "success"
        except Exception:
            return False


# Alias para compatibilidade
LLmInterface = LLMInterface
