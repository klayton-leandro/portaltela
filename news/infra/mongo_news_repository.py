
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from bson import ObjectId
from domain.interfaces import NewsRepositoryInterface
from infra.mongodb_infra import MongoDBInfra

try:
    from core.logging import log
except ImportError:
    from loguru import logger as log


class MongoNewsRepository(NewsRepositoryInterface):
    """
    Repositório de notícias implementado com MongoDB
    Implementa apenas operações de notícias (Interface Segregation)
    """

    COLLECTION = "news"

    def __init__(self, db: MongoDBInfra = None):
        """
        Inicializa o repositório

        Args:
            db: Instância de MongoDBInfra (injetada)
        """
        self._db = db or MongoDBInfra()

    def save(self, news_data: Dict[str, Any]) -> str:
        """Salva uma nova notícia"""
        news_data['created_at'] = datetime.now(timezone.utc)
        news_data['wordpress_published'] = False
        news_data['wordpress_post_id'] = None
        news_data['wordpress_url'] = None
        news_data['publish_error'] = None
        return self._db.insert_one(self.COLLECTION, news_data)

    def find_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Busca notícia pela URL"""
        return self._db.find_by_url(self.COLLECTION, url)

    def find_by_id(self, mongodb_id: str) -> Optional[Dict[str, Any]]:
        """Busca notícia pelo ID do MongoDB"""
        try:
            result = self._db.db[self.COLLECTION].find_one(
                {'_id': ObjectId(mongodb_id)}
            )
            if result:
                result['_id'] = str(result['_id'])
            return result
        except Exception as e:
            log.error(f"Erro ao buscar por ID: {e}")
            return None

    def update_by_url(self, url: str, news_data: Dict[str, Any]) -> bool:
        """Atualiza notícia existente pela URL"""
        news_data['updated_at'] = datetime.now(timezone.utc)
        modified = self._db.update_one(
            self.COLLECTION, {'url': url}, news_data)
        return modified > 0

    def upsert(self, url: str, news_data: Dict[str, Any]) -> str:
        """Insere ou atualiza uma notícia"""
        existing = self.find_by_url(url)

        if existing:
            self.update_by_url(url, news_data)
            log.info(f"Notícia atualizada: {existing['_id']}")
            return existing['_id']
        else:
            result_id = self.save(news_data)
            log.info(f"Notícia criada: {result_id}")
            return result_id

    def list_recent(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Lista as notícias mais recentes"""
        return self._db.find_many(self.COLLECTION, {}, limit=limit)

    def mark_as_published(
        self,
        mongodb_id: str,
        post_id: int,
        post_url: str
    ) -> bool:
        """
        Marca uma notícia como publicada no WordPress

        Args:
            mongodb_id: ID do documento
            post_id: ID do post no WordPress
            post_url: URL do post publicado

        Returns:
            True se atualizado com sucesso
        """
        try:
            result = self._db.db[self.COLLECTION].update_one(
                {'_id': ObjectId(mongodb_id)},
                {
                    '$set': {
                        'wordpress_published': True,
                        'wordpress_post_id': post_id,
                        'wordpress_url': post_url,
                        'wordpress_published_at': datetime.now(timezone.utc),
                        'publish_error': None
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            log.error(f"Erro ao marcar como publicado: {e}")
            return False

    def mark_publish_error(self, mongodb_id: str, error: str) -> bool:
        """
        Registra erro de publicação

        Args:
            mongodb_id: ID do documento
            error: Mensagem de erro

        Returns:
            True se atualizado com sucesso
        """
        try:
            result = self._db.db[self.COLLECTION].update_one(
                {'_id': ObjectId(mongodb_id)},
                {
                    '$set': {
                        'publish_error': error,
                        'publish_error_at': datetime.now(timezone.utc)
                    },
                    '$inc': {
                        'publish_attempts': 1
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            log.error(f"Erro ao registrar erro de publicação: {e}")
            return False

    def find_pending_publish(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Busca notícias que ainda não foram publicadas no WordPress

        Args:
            limit: Número máximo de resultados

        Returns:
            Lista de notícias pendentes
        """
        try:
            results = list(
                self._db.db[self.COLLECTION].find(
                    {
                        'wordpress_published': {'$ne': True},
                        'status': 'success',  # Apenas notícias processadas com sucesso
                        '$or': [
                            {'publish_attempts': {'$exists': False}},
                            # Máximo 3 tentativas
                            {'publish_attempts': {'$lt': 3}}
                        ]
                    }
                ).sort('created_at', -1).limit(limit)
            )
            for r in results:
                r['_id'] = str(r['_id'])
            return results
        except Exception as e:
            log.error(f"Erro ao buscar pendentes: {e}")
            return []

    def find_published(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Busca notícias já publicadas no WordPress

        Args:
            limit: Número máximo de resultados

        Returns:
            Lista de notícias publicadas
        """
        try:
            results = list(
                self._db.db[self.COLLECTION].find(
                    {'wordpress_published': True}
                ).sort('wordpress_published_at', -1).limit(limit)
            )
            for r in results:
                r['_id'] = str(r['_id'])
            return results
        except Exception as e:
            log.error(f"Erro ao buscar publicadas: {e}")
            return []

    def get_publish_stats(self) -> Dict[str, int]:
        """
        Retorna estatísticas de publicação

        Returns:
            Dicionário com contagens
        """
        try:
            total = self._db.db[self.COLLECTION].count_documents({})
            published = self._db.db[self.COLLECTION].count_documents(
                {'wordpress_published': True}
            )
            pending = self._db.db[self.COLLECTION].count_documents(
                {
                    'wordpress_published': {'$ne': True},
                    'status': 'success'
                }
            )
            errors = self._db.db[self.COLLECTION].count_documents(
                {'publish_error': {'$ne': None}}
            )

            return {
                "total": total,
                "published": published,
                "pending": pending,
                "with_errors": errors
            }
        except Exception as e:
            log.error(f"Erro ao obter stats: {e}")
            return {"error": str(e)}

    def close(self):
        """Fecha a conexão com o banco"""
        self._db.close()
