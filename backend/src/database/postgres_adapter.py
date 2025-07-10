# adapters/postgres_adapter.py
from sqlalchemy import create_engine, text, Table, MetaData, select, update, delete, and_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from config.config import db_settings
from typing import Any, Dict, List, Optional, Union

class PostgresAdapter:
    """
    Adapter for interacting with a PostgreSQL database using SQLAlchemy.

    This class provides utility methods to connect to a PostgreSQL database,
    reflect existing schemas, and perform basic CRUD operations on dynamically
    discovered tables. It caches fully qualified table names for performance.

    Typical usage:
        adapter = PostgresAdapter()
        adapter.connect()
        data = adapter.get_by_id("public.users", 1)
        adapter.disconnect()
    """
    def __init__(self):
        """
        Initializes the adapter without connecting.
        Use `connect()` to establish the connection.
        """
        self.engine = None
        self.SessionLocal = None
        self.metadata = MetaData()
        self.tables_cache = {}
        
    def connect(self) -> None:
        """
        Establishes a connection to the PostgreSQL database using
        environment variables defined in `db_settings`. Reflects all
        existing schemas and builds a cache of fully-qualified table names.
        """
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
        
        self.metadata.reflect(bind=self.engine)
        
        for table in self.metadata.tables.values():
            full_name = f"{table.schema}.{table.name}" if table.schema else table.name
            self.tables_cache[full_name] = table
    
    def disconnect(self) -> None:
        """
        Disposes of the active database connection.
        """
        if self.engine:
            self.engine.dispose()
    
    def _get_table(self, full_table_name: str) -> Table:
        """
        Retrieves a SQLAlchemy Table object by its fully-qualified name.

        :param full_table_name: Schema-qualified table name (e.g., "schema.table")
        :return: SQLAlchemy Table object
        :raises ValueError: If the table name is not valid or cannot be found
        """
        if full_table_name not in self.tables_cache:
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
        """
        Inserts a new row into the given table and returns the generated ID.

        :param table: Fully-qualified table name
        :param data: Dictionary containing column-value pairs
        :return: ID of the inserted record
        """
        tbl = self._get_table(table)
        with self.engine.begin() as connection:
            stmt = tbl.insert().values(**data).returning(tbl.c.id)
            result = connection.execute(stmt)
            return result.scalar()
    
    def update(self, table: str, id: Any, data: Dict[str, Any]) -> bool:
        """
        Updates a record by its ID in the given table.

        :param table: Fully-qualified table name
        :param id: Primary key ID of the record to update
        :param data: Dictionary of columns and new values
        :return: True if the record was updated, False otherwise
        """
        tbl = self._get_table(table)
        with self.engine.begin() as connection:
            stmt = update(tbl).where(tbl.c.id == id).values(**data)
            result = connection.execute(stmt)
            return result.rowcount > 0
    
    def delete(self, table: str, id: Any) -> bool:
        """
        Deletes a record by its ID from the given table.

        :param table: Fully-qualified table name
        :param id: ID of the record to delete
        :return: True if the record was deleted, False otherwise
        """
        tbl = self._get_table(table)
        with self.engine.begin() as connection:
            stmt = delete(tbl).where(tbl.c.id == id)
            result = connection.execute(stmt)
            return result.rowcount > 0
    
    def get_by_id(self, table: str, id: Any) -> Optional[Dict[str, Any]]:
        """
        Retrieves a single record by ID from the given table.

        :param table: Fully-qualified table name
        :param id: ID of the record to fetch
        :return: Dictionary representing the row, or None if not found
        """
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
        """
        Retrieves all rows from a table, optionally applying filters, limit, and offset.

        :param table: Fully-qualified table name
        :param filters: Dictionary of column-value pairs to filter on
        :param limit: Maximum number of rows to return
        :param offset: Number of rows to skip
        :return: List of dictionaries, each representing a row
        """
        tbl = self._get_table(table)
        stmt = select(tbl)
        
        if filters:
            conditions = []
            for key, value in filters.items():
                if hasattr(tbl.c, key):
                    column = getattr(tbl.c, key)
                    conditions.append(column == value)
            
            if conditions:
                stmt = stmt.where(and_(*conditions))
        
        if limit is not None:
            stmt = stmt.limit(limit)
            
        if offset is not None:
            stmt = stmt.offset(offset)
        
        with self.engine.connect() as connection:
            result = connection.execute(stmt)
            return [dict(row) for row in result.mappings()]
        
    def execute_raw(self, query: str, params: Optional[dict] = None) -> List[Dict[str, Any]]:
        """
        Executes a raw SQL query with optional parameters.

        :param query: SQL query string
        :param params: Optional dictionary of named parameters
        :return: List of dictionaries representing the result rows
        """
        with self.engine.connect() as connection:
            result = connection.execute(text(query), params or {})
            return [dict(row) for row in result.mappings()]
    
    def get_by_id_with_region(self, table: str, id: Any, region: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a record by its ID and region, assuming the table is partitioned by region.

        :param table: Fully-qualified table name
        :param id: Primary key ID of the record
        :param region: Region value to filter
        :return: Dictionary representing the row, or None if not found
        """
        tbl = self._get_table(table)
        with self.engine.connect() as connection:
            stmt = select(tbl).where(
                tbl.c.id == id,
                tbl.c.region == region
            )
            result = connection.execute(stmt)
            row = result.mappings().first()
            return dict(row) if row else None
