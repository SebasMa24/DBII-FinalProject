import redis
import json
from typing import Any, Dict, List, Optional, Union
from config.config import db_settings
from .base_database import DatabaseAdapter

class RedisAdapter(DatabaseAdapter):
    def __init__(self):
        self.client = None
        self.connection_params = None
        
    def connect(self) -> None:
        """Establece conexión con Redis"""
        self.client = redis.Redis(
            host=db_settings.redis_host,
            port=int(db_settings.redis_port),
            db=int(db_settings.redis_db),
            decode_responses=True
        )
        # Verificar conexión
        if not self.client.ping():
            raise ConnectionError("Failed to connect to Redis")
    
    def disconnect(self) -> None:
        """Cierra la conexión con Redis"""
        if self.client:
            self.client.close()
    
    def execute_query(self, query: str, params: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Ejecuta un comando personalizado de Redis.
        Ejemplo: query="HGETALL", params={"key": "user:1"}
        """
        if not self.client:
            raise ConnectionError("Redis client not connected")
        
        # Convertir parámetros a lista para ejecución
        args = []
        if params:
            for key, value in params.items():
                args.extend([key, value])
        
        # Ejecutar comando
        result = self.client.execute_command(query, *args)
        
        # Convertir resultados a formato consistente
        return self._parse_redis_result(result)
    
    def insert(self, table: str, data: Dict[str, Any]) -> Any:
        """
        Inserta datos como un hash en Redis.
        Retorna la clave generada.
        """
        key = f"{table}:{data.get('id', 'new')}"
        if not self.client.hset(key, mapping=data):
            raise ValueError(f"Failed to insert data with key: {key}")
        return key
    
    def update(self, table: str, id: Any, data: Dict[str, Any]) -> bool:
        """Actualiza un hash existente en Redis"""
        key = f"{table}:{id}"
        if not self.client.exists(key):
            return False
        return self.client.hset(key, mapping=data) > 0
    
    def delete(self, table: str, id: Any) -> bool:
        """Elimina una clave de Redis"""
        key = f"{table}:{id}"
        return self.client.delete(key) > 0
    
    def delete(self, table: str) -> None:
        """Elimina todas las claves de Redis asociadas a una tabla específica"""
        keys = self.client.keys(f"{table}:*")
        if keys:
            self.client.delete(*keys)
    
    def get_by_id(self, table: str, id: Any) -> Optional[Dict[str, Any]]:
        """Obtiene un hash por su clave"""
        key = f"{table}:{id}"
        if not self.client.exists(key):
            return None
        return self.client.hgetall(key)
    
    def get_all(self, table: str, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Obtiene todos los elementos de un tipo (patrón de clave)
        Los filtros no se aplican directamente en Redis, se procesan después
        """
        pattern = f"{table}:*"
        keys = self.client.keys(pattern)
        
        # Obtener todos los hashes
        results = []
        for key in keys:
            data = self.client.hgetall(key)
            data['_key'] = key  # Añadir clave para referencia
            results.append(data)
        
        # Aplicar filtros si existen
        if filters:
            return self._apply_filters(results, filters)
        return results
    
    def set_value(self, key: str, value: Any, ttl: int = None) -> bool:
        """Establece un valor simple (cadena, número, etc.)"""
        serialized = json.dumps(value)
        result = self.client.set(key, serialized)
        if ttl:
            self.client.expire(key, ttl)
        return result
    
    def get_value(self, key: str) -> Any:
        """Obtiene un valor simple"""
        value = self.client.get(key)
        return json.loads(value) if value else None
    
    def set_hash(self, key: str, data: Dict[str, Any], ttl: int = None) -> bool:
        """Establece un hash directamente con una clave personalizada"""
        result = self.client.hset(key, mapping=data)
        if ttl:
            self.client.expire(key, ttl)
        return result
    
    def get_hash(self, key: str) -> Dict[str, Any]:
        """Obtiene un hash completo por su clave"""
        return self.client.hgetall(key)
    
    def key_exists(self, key: str) -> bool:
        """Verifica si una clave existe"""
        return self.client.exists(key) > 0
    
    def set_expiration(self, key: str, ttl: int) -> bool:
        """Establece un tiempo de expiración para una clave"""
        return self.client.expire(key, ttl)
    
    def increment_counter(self, key: str, amount: int = 1) -> int:
        """Incrementa un contador atómico"""
        return self.client.incrby(key, amount)
    
    def add_to_set(self, key: str, *values: Any) -> int:
        """Añade valores a un conjunto"""
        return self.client.sadd(key, *values)
    
    def get_set(self, key: str) -> List[Any]:
        """Obtiene todos los valores de un conjunto"""
        return list(self.client.smembers(key))
    
    def publish(self, channel: str, message: Any) -> int:
        """Publica un mensaje en un canal Pub/Sub"""
        return self.client.publish(channel, json.dumps(message))
    
    def _apply_filters(self, data: List[Dict], filters: Dict) -> List[Dict]:
        """Filtra los resultados en memoria basado en criterios"""
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
        """Convierte resultados de Redis a formato consistente"""
        if isinstance(result, list):
            # Para resultados como HGETALL que vienen en lista plana [k1, v1, k2, v2]
            if len(result) % 2 == 0:
                return [{result[i]: result[i+1] for i in range(0, len(result), 2)}]
            return result
        elif isinstance(result, dict):
            return [result]
        elif result is None:
            return []
        return [{"result": result}]