# adapters/postgres_adapter.py
from sqlalchemy import create_engine, text, Table, MetaData, select, update, delete, and_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from config.config import db_settings
from typing import Any, Dict, List, Optional, Union

class PostgresAdapter:
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self.metadata = MetaData()
        self.tables_cache = {}
        
    def connect(self) -> None:
        connection_string = (
            f"postgresql://{db_settings.postgres_user}:"
            f"{db_settings.postgres_password}@"
            f"{db_settings.postgres_host}:"
            f"{db_settings.postgres_port}/"
            f"{db_settings.postgres_db}"
        )
        self.engine = create_engine(connection_string)
        self.SessionLocal = sessionmaker(
            autocommit=False, 
            autoflush=False, 
            bind=self.engine
        )
        # Reflejar TODOS los esquemas
        self.metadata.reflect(bind=self.engine)
        
        # Construir cache de nombres completos
        for table in self.metadata.tables.values():
            full_name = f"{table.schema}.{table.name}" if table.schema else table.name
            self.tables_cache[full_name] = table
    
    def disconnect(self) -> None:
        if self.engine:
            self.engine.dispose()
    
    def _get_table(self, full_table_name: str) -> Table:
        """Obtiene la tabla del cache usando nombre completo esquema.tabla"""
        if full_table_name not in self.tables_cache:
            # Intentar cargar la tabla específica
            parts = full_table_name.split('.')
            if len(parts) == 2:
                schema, table_name = parts
                table = Table(
                    table_name, 
                    self.metadata, 
                    schema=schema,
                    autoload_with=self.engine
                )
                self.tables_cache[full_table_name] = table
            else:
                raise ValueError(f"Invalid table name format: {full_table_name}. Use 'schema.table'")
        
        return self.tables_cache[full_table_name]
    
    def insert(self, table: str, data: Dict[str, Any]) -> Any:
        tbl = self._get_table(table)
        with self.engine.begin() as connection:
            stmt = tbl.insert().values(**data).returning(tbl.c.id)
            result = connection.execute(stmt)
            return result.scalar()
    
    def update(self, table: str, id: Any, data: Dict[str, Any]) -> bool:
        tbl = self._get_table(table)
        with self.engine.begin() as connection:
            stmt = update(tbl).where(tbl.c.id == id).values(**data)
            result = connection.execute(stmt)
            return result.rowcount > 0
    
    def delete(self, table: str, id: Any) -> bool:
        tbl = self._get_table(table)
        with self.engine.begin() as connection:
            stmt = delete(tbl).where(tbl.c.id == id)
            result = connection.execute(stmt)
            return result.rowcount > 0
    
    def get_by_id(self, table: str, id: Any) -> Optional[Dict[str, Any]]:
        tbl = self._get_table(table)
        with self.engine.connect() as connection:
            stmt = select(tbl).where(tbl.c.id == id)
            result = connection.execute(stmt)
            row = result.mappings().first()
            return dict(row) if row else None
    
    def get_all(
        self, 
        table: str, 
        filters: Optional[Dict] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        tbl = self._get_table(table)
        stmt = select(tbl)
        
        if filters:
            # Crear condiciones correctamente
            conditions = []
            for key, value in filters.items():
                if hasattr(tbl.c, key):
                    column = getattr(tbl.c, key)
                    conditions.append(column == value)
            
            if conditions:
                # Combinar condiciones con AND
                stmt = stmt.where(and_(*conditions))
        
        if limit is not None:
            stmt = stmt.limit(limit)
            
        if offset is not None:
            stmt = stmt.offset(offset)
        
        with self.engine.connect() as connection:
            result = connection.execute(stmt)
            return [dict(row) for row in result.mappings()]
        
    def execute_raw(self, query: str, params: Optional[dict] = None) -> List[Dict[str, Any]]:
        with self.engine.connect() as connection:
            result = connection.execute(text(query), params or {})
            return [dict(row) for row in result.mappings()]
    
    def get_by_id_with_region(self, table: str, id: Any, region: str) -> Optional[Dict[str, Any]]:
        tbl = self._get_table(table)
        with self.engine.connect() as connection:
            stmt = select(tbl).where(
                tbl.c.id == id,
                tbl.c.region == region
            )
            result = connection.execute(stmt)
            row = result.mappings().first()
            return dict(row) if row else None
