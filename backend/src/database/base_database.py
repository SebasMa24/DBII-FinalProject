from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class DatabaseAdapter(ABC):
    """
    Abstract base class defining a common interface for interacting with databases.

    This interface ensures consistency across different types of database backends,
    such as SQL or NoSQL implementations.

    Implementing classes must provide concrete methods for connecting, disconnecting,
    and performing basic CRUD operations.
    """

    @abstractmethod
    def connect(self, **kwargs) -> None:
        """
        Establishes a connection to the database.
        
        Implementing classes can use additional keyword arguments as needed.
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """
        Closes the connection to the database.
        """
        pass

    @abstractmethod
    def insert(self, table: str, data: Dict[str, Any]) -> Any:
        """
        Inserts a new record/document into the specified table or collection.

        :param table: The name of the table or collection.
        :param data: The data to insert as a dictionary.
        :return: The identifier of the inserted record/document.
        """
        pass

    @abstractmethod
    def update(self, table: str, id: Any, data: Dict[str, Any]) -> bool:
        """
        Updates a record/document by its ID.

        :param table: The name of the table or collection.
        :param id: The identifier of the record/document to update.
        :param data: Dictionary with updated data.
        :return: True if the record was updated, False otherwise.
        """
        pass

    @abstractmethod
    def delete(self, table: str, id: Any) -> bool:
        """
        Deletes a record/document by its ID.

        :param table: The name of the table or collection.
        :param id: The identifier of the record/document to delete.
        :return: True if the record was deleted, False otherwise.
        """
        pass

    @abstractmethod
    def get_by_id(self, table: str, id: Any) -> Optional[Dict[str, Any]]:
        """
        Retrieves a record/document by its ID.

        :param table: The name of the table or collection.
        :param id: The identifier of the record/document.
        :return: The record as a dictionary, or None if not found.
        """
        pass

    @abstractmethod
    def get_all(self, table: str, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Retrieves all records/documents from the specified table or collection.

        :param table: The name of the table or collection.
        :param filters: Optional filtering conditions as a dictionary.
        :return: A list of matching records/documents.
        """
        pass
