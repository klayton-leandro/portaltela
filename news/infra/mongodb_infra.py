import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

try:
    from core.logging import log
except ImportError:
    from loguru import logger as log


class MongoDBInfra:
    """Classe para gerenciar conexão e operações com MongoDB"""

    DEFAULT_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/")
    DEFAULT_DB = os.environ.get("MONGODB_DB", "news_feed_db")

    def __init__(self, uri: str = None, db_name: str = None):
        self.uri = uri or self.DEFAULT_URI
        self.db_name = db_name or self.DEFAULT_DB
        self.client = None
        self.db = None
        self._connect()

    def _connect(self):
        """Estabelece conexão com o MongoDB"""
        try:
            self.client = MongoClient(self.uri, serverSelectionTimeoutMS=5000)
            # Testa a conexão
            self.client.admin.command('ping')
            self.db = self.client[self.db_name]
            log.info(f"Conectado ao MongoDB: {self.db_name}")
        except ConnectionFailure as e:
            log.error(f"Falha ao conectar ao MongoDB: {e}")
            raise

    def insert_one(self, collection_name: str, document: Dict[str, Any]) -> str:
        """Insere um documento na coleção"""
        collection = self.db[collection_name]
        # Adiciona timestamp de criação
        document['created_at'] = datetime.now(timezone.utc)
        result = collection.insert_one(document)
        return str(result.inserted_id)

    def insert_many(self, collection_name: str, documents: List[Dict[str, Any]]) -> List[str]:
        """Insere múltiplos documentos na coleção"""
        collection = self.db[collection_name]
        for doc in documents:
            doc['created_at'] = datetime.now(timezone.utc)
        result = collection.insert_many(documents)
        return [str(id) for id in result.inserted_ids]

    def find_one(self, collection_name: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Busca um documento na coleção"""
        collection = self.db[collection_name]
        result = collection.find_one(query)
        if result:
            result['_id'] = str(result['_id'])
        return result

    def find_many(self, collection_name: str, query: Dict[str, Any] = None,
                  limit: int = 100) -> List[Dict[str, Any]]:
        """Busca múltiplos documentos na coleção"""
        collection = self.db[collection_name]
        query = query or {}
        results = list(collection.find(query).limit(limit))
        for result in results:
            result['_id'] = str(result['_id'])
        return results

    def find_by_url(self, collection_name: str, url: str) -> Optional[Dict[str, Any]]:
        """Busca um documento pelo URL"""
        return self.find_one(collection_name, {'url': url})

    def update_one(self, collection_name: str, query: Dict[str, Any],
                   update: Dict[str, Any]) -> int:
        """Atualiza um documento na coleção"""
        collection = self.db[collection_name]
        update['updated_at'] = datetime.now(timezone.utc)
        result = collection.update_one(query, {'$set': update})
        return result.modified_count

    def upsert_one(self, collection_name: str, query: Dict[str, Any],
                   document: Dict[str, Any]) -> str:
        """Insere ou atualiza um documento"""
        collection = self.db[collection_name]
        document['updated_at'] = datetime.now(timezone.utc)
        result = collection.update_one(query, {'$set': document}, upsert=True)
        if result.upserted_id:
            return str(result.upserted_id)
        return "updated"

    def delete_one(self, collection_name: str, query: Dict[str, Any]) -> int:
        """Remove um documento da coleção"""
        collection = self.db[collection_name]
        result = collection.delete_one(query)
        return result.deleted_count

    def count(self, collection_name: str, query: Dict[str, Any] = None) -> int:
        """Conta documentos na coleção"""
        collection = self.db[collection_name]
        query = query or {}
        return collection.count_documents(query)

    def close(self):
        """Fecha a conexão com o MongoDB"""
        if self.client:
            self.client.close()
            log.debug("Conexão com MongoDB fechada")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
