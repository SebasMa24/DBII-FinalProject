import redis
import json
from typing import Any, Dict, List, Optional, Union
from config.config import db_settings
from .base_database import DatabaseAdapter

class RedisAdapter(DatabaseAdapter):
    """
    Adapter for interacting with a Redis database.

    This class provides methods to connect to Redis and perform operations such as
    inserting, updating, retrieving, and deleting key-value pairs, hashes, and sets.
    It supports Redis hash-based storage and simple value operations, with optional
    filtering logic applied in memory.

    Typical usage:
        adapter = RedisAdapter()
        adapter.connect()
        adapter.insert("users", {"id": 1, "name": "Alice"})
        data = adapter.get_by_id("users", 1)
        adapter.disconnect()
    """

    def __init__(self):
        self.client = None
        self.connection_params = None
        
    def connect(self) -> None:
        """Establishes a connection to the Redis server."""
        self.client = redis.Redis(
            host=db_settings.redis_host,
            port=int(db_settings.redis_port),
            db=int(db_settings.redis_db),
            decode_responses=True
        )
        if not self.client.ping():
            raise ConnectionError("Failed to connect to Redis")
    
    def disconnect(self) -> None:
        """Closes the connection to the Redis server."""
        if self.client:
            self.client.close()
    
    def execute_query(self, query: str, params: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Executes a raw Redis command.

        Args:
            query: Redis command string (e.g., "HGETALL").
            params: Optional dictionary with key-value arguments for the command.

        Returns:
            A list of results in dictionary format.
        """
        if not self.client:
            raise ConnectionError("Redis client not connected")
        
        args = []
        if params:
            for key, value in params.items():
                args.extend([key, value])
        
        result = self.client.execute_command(query, *args)
        
        return self._parse_redis_result(result)
    
    def insert(self, table: str, data: Dict[str, Any]) -> Any:
        """
        Inserts data as a Redis hash.

        Args:
            table: Prefix or namespace for the key.
            data: Dictionary of data to store.

        Returns:
            The Redis key used for storage.
        """
        key = f"{table}:{data.get('id', 'new')}"
        if not self.client.hset(key, mapping=data):
            raise ValueError(f"Failed to insert data with key: {key}")
        return key
    
    def update(self, table: str, id: Any, data: Dict[str, Any]) -> bool:
        """
        Updates an existing hash in Redis.

        Args:
            table: Table name (used as prefix).
            id: Identifier to locate the hash.
            data: Dictionary with updated fields.

        Returns:
            True if update is successful, False otherwise.
        """
        key = f"{table}:{id}"
        if not self.client.exists(key):
            return False
        return self.client.hset(key, mapping=data) > 0
    
    def delete(self, table: str, id: Any) -> bool:
        """
        Deletes a single Redis key.

        Args:
            table: Table name (prefix).
            id: ID to form the key.

        Returns:
            True if the key was deleted, False otherwise.
        """
        key = f"{table}:{id}"
        return self.client.delete(key) > 0
    
    def delete(self, table: str) -> None:
        """
        Deletes all Redis keys.

        Args:
            table: Table name (prefix).

        Returns:
            True if the key was deleted, False otherwise.
        """
        keys = self.client.keys(f"{table}:*")
        if keys:
            self.client.delete(*keys)
    
    def get_by_id(self, table: str, id: Any) -> Optional[Dict[str, Any]]:
        """
        Retrieves a hash by its key.

        Args:
            table: Table name (prefix).
            id: ID used to construct the Redis key.

        Returns:
            Dictionary of fields, or None if the key doesn't exist.
        """
        key = f"{table}:{id}"
        if not self.client.exists(key):
            return None
        return self.client.hgetall(key)
    
    def get_all(self, table: str, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Retrieves all hashes with the given prefix, optionally filtered.

        Args:
            table: Prefix used to scan Redis keys.
            filters: Dictionary of fields to filter in memory.

        Returns:
            A list of hash dictionaries.
        """
        pattern = f"{table}:*"
        keys = self.client.keys(pattern)
        
        results = []
        for key in keys:
            data = self.client.hgetall(key)
            data['_key'] = key 
            results.append(data)
        
        if filters:
            return self._apply_filters(results, filters)
        return results
    
    def set_value(self, key: str, value: Any, ttl: int = None) -> bool:
        """
        Sets a simple value (string, number, etc.) with optional expiration.

        Args:
            key: Redis key.
            value: Value to store.
            ttl: Time-to-live in seconds (optional).

        Returns:
            True if successful.
        """
        serialized = json.dumps(value)
        result = self.client.set(key, serialized)
        if ttl:
            self.client.expire(key, ttl)
        return result
    
    def get_value(self, key: str) -> Any:
        """
        Gets a simple value from Redis.

        Args:
            key: Redis key.

        Returns:
            Deserialized value, or None if key not found.
        """
        value = self.client.get(key)
        return json.loads(value) if value else None
    
    def set_hash(self, key: str, data: Dict[str, Any], ttl: int = None) -> bool:
        """
        Sets a hash directly in Redis.

        Args:
            key: Redis key.
            data: Dictionary of fields and values.
            ttl: Optional expiration time in seconds.

        Returns:
            True if successful.
        """
        result = self.client.hset(key, mapping=data)
        if ttl:
            self.client.expire(key, ttl)
        return result
    
    def get_hash(self, key: str) -> Dict[str, Any]:
        """
        Retrieves a full hash from Redis.

        Args:
            key: Redis key.

        Returns:
            Dictionary of fields and values.
        """
        return self.client.hgetall(key)
    
    def key_exists(self, key: str) -> bool:
        """Checks whether a given key exists in Redis."""
        return self.client.exists(key) > 0
    
    def set_expiration(self, key: str, ttl: int) -> bool:
        """Sets an expiration time (in seconds) on a key."""
        return self.client.expire(key, ttl)
    
    def increment_counter(self, key: str, amount: int = 1) -> int:
        """
        Atomically increments a counter.

        Args:
            key: Redis key.
            amount: Value to increment by.

        Returns:
            New counter value.
        """
        return self.client.incrby(key, amount)
    
    def add_to_set(self, key: str, *values: Any) -> int:
        """
        Adds one or more values to a Redis set.

        Args:
            key: Redis key.
            values: Values to add.

        Returns:
            Number of new elements added to the set.
        """
        return self.client.sadd(key, *values)
    
    def get_set(self, key: str) -> List[Any]:
        """
        Retrieves all members of a Redis set.

        Args:
            key: Redis key.

        Returns:
            List of values.
        """
        return list(self.client.smembers(key))
    
    def publish(self, channel: str, message: Any) -> int:
        """
        Publishes a message to a Redis Pub/Sub channel.

        Args:
            channel: Channel name.
            message: Message to send.

        Returns:
            Number of clients that received the message.
        """
        return self.client.publish(channel, json.dumps(message))
    
    def _apply_filters(self, data: List[Dict], filters: Dict) -> List[Dict]:
        """
        Applies filter logic in-memory on Redis hash results.

        Args:
            data: List of dictionaries to filter.
            filters: Dictionary of filtering conditions.

        Returns:
            Filtered list of dictionaries.
        """
        filtered = []
        for item in data:
            match = True
            for key, value in filters.items():
                if item.get(key) != value:
                    match = False
                    break
            if match:
                filtered.append(item)
        return filtered
    
    def _parse_redis_result(self, result) -> List[Dict[str, Any]]:
        """
        Normalizes raw Redis responses into structured dictionaries.

        Args:
            result: Raw result from a Redis command.

        Returns:
            A list of dictionaries with consistent formatting.
        """
        if isinstance(result, list):
            if len(result) % 2 == 0:
                return [{result[i]: result[i+1] for i in range(0, len(result), 2)}]
            return result
        elif isinstance(result, dict):
            return [result]
        elif result is None:
            return []
        return [{"result": result}]