from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class DatabaseAdapter(ABC):
    @abstractmethod
    def connect(self, **kwargs) -> None:
        pass

    @abstractmethod
    def disconnect(self) -> None:
        pass

    @abstractmethod
    def insert(self, table: str, data: Dict[str, Any]) -> Any:
        pass

    @abstractmethod
    def update(self, table: str, id: Any, data: Dict[str, Any]) -> bool:
        pass

    @abstractmethod
    def delete(self, table: str, id: Any) -> bool:
        pass

    @abstractmethod
    def get_by_id(self, table: str, id: Any) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_all(self, table: str, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        pass