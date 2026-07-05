# ============================================================
# services/base_service.py - Base Service
# ============================================================

from typing import Generic, TypeVar, Type, Optional, List, Dict, Any
from sqlalchemy.orm import Session
import logging

from app.repositories.base_repository import BaseRepository
from app.api.database import Base

logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType", bound=Base)
RepositoryType = TypeVar("RepositoryType", bound=BaseRepository)


class BaseService(Generic[ModelType, RepositoryType]):
    """
    Base service with common operations.
    """
    
    def __init__(self, repository: RepositoryType):
        self.repository = repository
        self.db = repository.db
    
    def get_all(self, **filters) -> List[ModelType]:
        """Get all records."""
        return self.repository.get_all(**filters)
    
    def get_by_id(self, id: int) -> Optional[ModelType]:
        """Get record by ID."""
        return self.repository.get_by_id(id)
    
    def get_paginated(self, page: int = 1, page_size: int = 20, **filters) -> Dict[str, Any]:
        """Get paginated records."""
        return self.repository.get_paginated(page, page_size, **filters)
    
    def create(self, **kwargs) -> ModelType:
        """Create a record."""
        return self.repository.create(**kwargs)
    
    def update(self, id: int, **kwargs) -> Optional[ModelType]:
        """Update a record."""
        return self.repository.update_by_id(id, **kwargs)
    
    def delete(self, id: int, soft_delete: bool = True) -> bool:
        """Delete a record."""
        return self.repository.delete_by_id(id, soft_delete)
    
    def count(self, **filters) -> int:
        """Count records."""
        return self.repository.count(**filters)
    
    def exists(self, **filters) -> bool:
        """Check if record exists."""
        return self.repository.exists(**filters)
    
    def search(self, search_term: str, **filters) -> List[ModelType]:
        """Search records."""
        # Override in child classes
        return self.get_all(**filters)