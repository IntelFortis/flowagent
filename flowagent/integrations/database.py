"""
Database - Database integrations for FlowAgent.

This module provides integrations with popular databases.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TypeVar, Union

from flowagent.core.logger import logger
from flowagent.core.exceptions import IntegrationError

T = TypeVar("T")


@dataclass
class DatabaseConfig:
    """Configuration for database connections."""
    connection_string: Optional[str] = None
    host: str = "localhost"
    port: Optional[int] = None
    database: str = ""
    username: str = ""
    password: str = ""
    pool_size: int = 5
    max_overflow: int = 10
    timeout: float = 30.0
    ssl: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class DatabaseProvider(ABC):
    """
    Abstract base class for database providers.

    All database integrations should inherit from this class.
    """

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._client = None
        self._connected = False

    @abstractmethod
    async def connect(self) -> None:
        """Connect to the database."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the database."""
        pass

    @abstractmethod
    async def execute(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Execute a query.

        Args:
            query: SQL or NoSQL query
            params: Query parameters

        Returns:
            Query result
        """
        pass

    @abstractmethod
    async def fetch_one(self, query: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Fetch a single row.

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            Row as dictionary or None
        """
        pass

    @abstractmethod
    async def fetch_all(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Fetch all rows.

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            List of rows as dictionaries
        """
        pass

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()


class PostgreSQL(DatabaseProvider):
    """
    PostgreSQL database provider.

    Example:
        >>> async with PostgreSQL(connection_string="postgresql://...") as db:
        ...     result = await db.fetch_all("SELECT * FROM users")
    """

    def __init__(self, config: Optional[DatabaseConfig] = None, **kwargs):
        if config is None:
            config = DatabaseConfig(**kwargs)
        super().__init__(config)

    async def connect(self) -> None:
        """Connect to PostgreSQL."""
        try:
            import asyncpg

            if self.config.connection_string:
                self._pool = await asyncpg.create_pool(
                    self.config.connection_string,
                    min_size=1,
                    max_size=self.config.pool_size,
                )
            else:
                self._pool = await asyncpg.create_pool(
                    host=self.config.host,
                    port=self.config.port or 5432,
                    database=self.config.database,
                    user=self.config.username,
                    password=self.config.password,
                    min_size=1,
                    max_size=self.config.pool_size,
                )

            self._connected = True
            logger.info("Connected to PostgreSQL")

        except ImportError:
            raise IntegrationError(
                "asyncpg package not installed. "
                "Install with: pip install flowagent[database]"
            )
        except Exception as e:
            raise IntegrationError(f"PostgreSQL connection failed: {e}") from e

    async def disconnect(self) -> None:
        """Disconnect from PostgreSQL."""
        if self._pool:
            await self._pool.close()
            self._connected = False
            logger.info("Disconnected from PostgreSQL")

    async def execute(self, query: str, params: Optional[Dict[str, Any]] = None) -> str:
        """Execute a query."""
        async with self._pool.acquire() as conn:
            if params:
                result = await conn.execute(query, *params.values())
            else:
                result = await conn.execute(query)
            return result

    async def fetch_one(self, query: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Fetch a single row."""
        async with self._pool.acquire() as conn:
            if params:
                row = await conn.fetchrow(query, *params.values())
            else:
                row = await conn.fetchrow(query)

            if row:
                return dict(row)
            return None

    async def fetch_all(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Fetch all rows."""
        async with self._pool.acquire() as conn:
            if params:
                rows = await conn.fetch(query, *params.values())
            else:
                rows = await conn.fetch(query)

            return [dict(row) for row in rows]


class MySQL(DatabaseProvider):
    """
    MySQL database provider.

    Example:
        >>> async with MySQL(host="localhost", database="mydb") as db:
        ...     result = await db.fetch_all("SELECT * FROM users")
    """

    def __init__(self, config: Optional[DatabaseConfig] = None, **kwargs):
        if config is None:
            config = DatabaseConfig(**kwargs)
        super().__init__(config)

    async def connect(self) -> None:
        """Connect to MySQL."""
        try:
            import aiomysql

            self._pool = await aiomysql.create_pool(
                host=self.config.host,
                port=self.config.port or 3306,
                db=self.config.database,
                user=self.config.username,
                password=self.config.password,
                minsize=1,
                maxsize=self.config.pool_size,
            )

            self._connected = True
            logger.info("Connected to MySQL")

        except ImportError:
            raise IntegrationError(
                "aiomysql package not installed. "
                "Install with: pip install flowagent[database]"
            )
        except Exception as e:
            raise IntegrationError(f"MySQL connection failed: {e}") from e

    async def disconnect(self) -> None:
        """Disconnect from MySQL."""
        if self._pool:
            self._pool.close()
            await self._pool.wait_closed()
            self._connected = False
            logger.info("Disconnected from MySQL")

    async def execute(self, query: str, params: Optional[Dict[str, Any]] = None) -> int:
        """Execute a query."""
        async with self._pool.acquire() as conn:
            async with conn.cursor() as cursor:
                if params:
                    await cursor.execute(query, params)
                else:
                    await cursor.execute(query)
                await conn.commit()
                return cursor.rowcount

    async def fetch_one(self, query: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Fetch a single row."""
        async with self._pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                if params:
                    await cursor.execute(query, params)
                else:
                    await cursor.execute(query)
                return await cursor.fetchone()

    async def fetch_all(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Fetch all rows."""
        async with self._pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                if params:
                    await cursor.execute(query, params)
                else:
                    await cursor.execute(query)
                return await cursor.fetchall()


class MongoDB(DatabaseProvider):
    """
    MongoDB database provider.

    Example:
        >>> async with MongoDB(connection_string="mongodb://...") as db:
        ...     result = await db.find("users", {"age": {"$gt": 25}})
    """

    def __init__(self, config: Optional[DatabaseConfig] = None, **kwargs):
        if config is None:
            config = DatabaseConfig(**kwargs)
        super().__init__(config)

    async def connect(self) -> None:
        """Connect to MongoDB."""
        try:
            from motor.motor_asyncio import AsyncIOMotorClient

            if self.config.connection_string:
                self._client = AsyncIOMotorClient(self.config.connection_string)
            else:
                self._client = AsyncIOMotorClient(
                    host=self.config.host,
                    port=self.config.port or 27017,
                    username=self.config.username or None,
                    password=self.config.password or None,
                )

            self._db = self._client[self.config.database]
            self._connected = True
            logger.info("Connected to MongoDB")

        except ImportError:
            raise IntegrationError(
                "motor package not installed. "
                "Install with: pip install flowagent[database]"
            )
        except Exception as e:
            raise IntegrationError(f"MongoDB connection failed: {e}") from e

    async def disconnect(self) -> None:
        """Disconnect from MongoDB."""
        if self._client:
            self._client.close()
            self._connected = False
            logger.info("Disconnected from MongoDB")

    async def execute(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Execute a MongoDB operation."""
        # MongoDB uses different query syntax
        raise NotImplementedError("Use find, insert, update, delete methods instead")

    async def fetch_one(self, query: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Fetch a single document."""
        collection = self._db[query]
        return await collection.find_one(params or {})

    async def fetch_all(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Fetch all documents."""
        collection = self._db[query]
        cursor = collection.find(params or {})
        return await cursor.to_list(length=None)

    async def find(
        self,
        collection: str,
        filter: Optional[Dict[str, Any]] = None,
        projection: Optional[Dict[str, Any]] = None,
        sort: Optional[List[tuple]] = None,
        limit: int = 0,
        skip: int = 0,
    ) -> List[Dict[str, Any]]:
        """Find documents in a collection."""
        coll = self._db[collection]
        cursor = coll.find(filter or {}, projection)

        if sort:
            cursor = cursor.sort(sort)
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)

        return await cursor.to_list(length=None)

    async def insert(self, collection: str, document: Dict[str, Any]) -> str:
        """Insert a document."""
        coll = self._db[collection]
        result = await coll.insert_one(document)
        return str(result.inserted_id)

    async def insert_many(self, collection: str, documents: List[Dict[str, Any]]) -> List[str]:
        """Insert multiple documents."""
        coll = self._db[collection]
        result = await coll.insert_many(documents)
        return [str(id) for id in result.inserted_ids]

    async def update(
        self,
        collection: str,
        filter: Dict[str, Any],
        update: Dict[str, Any],
        upsert: bool = False,
    ) -> int:
        """Update documents."""
        coll = self._db[collection]
        result = await coll.update_many(filter, update, upsert=upsert)
        return result.modified_count

    async def delete(self, collection: str, filter: Dict[str, Any]) -> int:
        """Delete documents."""
        coll = self._db[collection]
        result = await coll.delete_many(filter)
        return result.deleted_count


class Redis(DatabaseProvider):
    """
    Redis database provider.

    Example:
        >>> async with Redis(host="localhost") as db:
        ...     await db.set("key", "value")
        ...     value = await db.get("key")
    """

    def __init__(self, config: Optional[DatabaseConfig] = None, **kwargs):
        if config is None:
            config = DatabaseConfig(**kwargs)
        super().__init__(config)

    async def connect(self) -> None:
        """Connect to Redis."""
        try:
            import redis.asyncio as aioredis

            if self.config.connection_string:
                self._client = aioredis.from_url(self.config.connection_string)
            else:
                self._client = aioredis.Redis(
                    host=self.config.host,
                    port=self.config.port or 6379,
                    password=self.config.password or None,
                    db=int(self.config.database) if self.config.database else 0,
                )

            self._connected = True
            logger.info("Connected to Redis")

        except ImportError:
            raise IntegrationError(
                "redis package not installed. "
                "Install with: pip install flowagent[database]"
            )
        except Exception as e:
            raise IntegrationError(f"Redis connection failed: {e}") from e

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._client:
            await self._client.close()
            self._connected = False
            logger.info("Disconnected from Redis")

    async def execute(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Execute a Redis command."""
        return await self._client.execute_command(query, *(params or {}).values())

    async def fetch_one(self, query: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Not applicable for Redis."""
        raise NotImplementedError("Use get, hget, etc. methods instead")

    async def fetch_all(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Not applicable for Redis."""
        raise NotImplementedError("Use keys, hgetall, etc. methods instead")

    async def get(self, key: str) -> Optional[str]:
        """Get a value by key."""
        value = await self._client.get(key)
        if value:
            return value.decode("utf-8")
        return None

    async def set(
        self,
        key: str,
        value: str,
        ex: Optional[int] = None,
        px: Optional[int] = None,
    ) -> bool:
        """Set a key-value pair."""
        return await self._client.set(key, value, ex=ex, px=px)

    async def delete(self, key: str) -> bool:
        """Delete a key."""
        return await self._client.delete(key) > 0

    async def exists(self, key: str) -> bool:
        """Check if a key exists."""
        return await self._client.exists(key) > 0

    async def expire(self, key: str, seconds: int) -> bool:
        """Set key expiration."""
        return await self._client.expire(key, seconds)

    async def hget(self, name: str, key: str) -> Optional[str]:
        """Get a hash field value."""
        value = await self._client.hget(name, key)
        if value:
            return value.decode("utf-8")
        return None

    async def hset(self, name: str, key: str, value: str) -> int:
        """Set a hash field value."""
        return await self._client.hset(name, key, value)

    async def hgetall(self, name: str) -> Dict[str, str]:
        """Get all hash fields."""
        data = await self._client.hgetall(name)
        return {k.decode("utf-8"): v.decode("utf-8") for k, v in data.items()}


class Elasticsearch(DatabaseProvider):
    """
    Elasticsearch database provider.

    Example:
        >>> async with Elasticsearch(hosts=["localhost:9200"]) as db:
        ...     result = await db.search("my-index", {"query": {"match_all": {}}})
    """

    def __init__(self, config: Optional[DatabaseConfig] = None, **kwargs):
        if config is None:
            config = DatabaseConfig(**kwargs)
        super().__init__(config)

    async def connect(self) -> None:
        """Connect to Elasticsearch."""
        try:
            from elasticsearch import AsyncElasticsearch

            hosts = [self.config.host]
            if self.config.port:
                hosts = [f"{self.config.host}:{self.config.port}"]

            self._client = AsyncElasticsearch(
                hosts=hosts,
                http_auth=(
                    self.config.username,
                    self.config.password,
                ) if self.config.username else None,
                use_ssl=self.config.ssl,
            )

            # Test connection
            await self._client.info()
            self._connected = True
            logger.info("Connected to Elasticsearch")

        except ImportError:
            raise IntegrationError(
                "elasticsearch package not installed. "
                "Install with: pip install flowagent[database]"
            )
        except Exception as e:
            raise IntegrationError(f"Elasticsearch connection failed: {e}") from e

    async def disconnect(self) -> None:
        """Disconnect from Elasticsearch."""
        if self._client:
            await self._client.close()
            self._connected = False
            logger.info("Disconnected from Elasticsearch")

    async def execute(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Execute an Elasticsearch query."""
        raise NotImplementedError("Use search, index, etc. methods instead")

    async def fetch_one(self, query: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Fetch a single document by ID."""
        try:
            result = await self._client.get(index=query, id=params.get("id"))
            return result["_source"]
        except Exception:
            return None

    async def fetch_all(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Fetch all documents matching query."""
        result = await self._client.search(
            index=query,
            body=params or {"query": {"match_all": {}}},
        )
        return [hit["_source"] for hit in result["hits"]["hits"]]

    async def search(
        self,
        index: str,
        body: Dict[str, Any],
        size: int = 10,
        from_: int = 0,
    ) -> List[Dict[str, Any]]:
        """Search documents."""
        result = await self._client.search(
            index=index,
            body=body,
            size=size,
            from_=from_,
        )
        return [hit["_source"] for hit in result["hits"]["hits"]]

    async def index(
        self,
        index: str,
        document: Dict[str, Any],
        id: Optional[str] = None,
    ) -> str:
        """Index a document."""
        result = await self._client.index(
            index=index,
            body=document,
            id=id,
        )
        return result["_id"]

    async def update(
        self,
        index: str,
        id: str,
        document: Dict[str, Any],
    ) -> None:
        """Update a document."""
        await self._client.update(
            index=index,
            id=id,
            body={"doc": document},
        )

    async def delete(self, index: str, id: str) -> None:
        """Delete a document."""
        await self._client.delete(index=index, id=id)
