# ============================================================
# repositories/base_repository.py - Base CRUD Operations
# ============================================================

from typing import Generic, TypeVar, Type, Optional, List, Dict, Any, Union
from sqlalchemy.orm import Session, Query
from sqlalchemy import func, and_, or_, desc, asc
from datetime import datetime
import logging

from app.api.database import Base

logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Base repository with common CRUD operations.
    """
    
    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db
    
    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
        order_desc: bool = True,
        **filters
    ) -> List[ModelType]:
        """
        Get all records with pagination and filters.
        """
        query = self.db.query(self.model)
        
        # Apply filters
        for key, value in filters.items():
            if value is not None:
                query = query.filter(getattr(self.model, key) == value)
        
        # Apply ordering
        if order_by:
            order_field = getattr(self.model, order_by)
            if order_desc:
                query = query.order_by(desc(order_field))
            else:
                query = query.order_by(asc(order_field))
        else:
            query = query.order_by(desc(self.model.id))
        
        return query.offset(skip).limit(limit).all()
    
    def get_by_id(self, id: int) -> Optional[ModelType]:
        """Get record by ID."""
        return self.db.query(self.model).filter(self.model.id == id).first()
    
    def get_by_field(self, field: str, value: Any) -> Optional[ModelType]:
        """Get record by field value."""
        return self.db.query(self.model).filter(getattr(self.model, field) == value).first()
    
    def get_by_fields(self, **kwargs) -> Optional[ModelType]:
        """Get record by multiple fields."""
        query = self.db.query(self.model)
        for key, value in kwargs.items():
            query = query.filter(getattr(self.model, key) == value)
        return query.first()
    
    def get_multi_by_field(self, field: str, value: Any) -> List[ModelType]:
        """Get multiple records by field value."""
        return self.db.query(self.model).filter(getattr(self.model, field) == value).all()
    
    def create(self, **kwargs) -> ModelType:
        """Create a new record."""
        instance = self.model(**kwargs)
        self.db.add(instance)
        self.db.flush()
        return instance
    
    def create_bulk(self, items: List[Dict[str, Any]]) -> List[ModelType]:
        """Create multiple records."""
        instances = [self.model(**item) for item in items]
        self.db.add_all(instances)
        self.db.flush()
        return instances
    
    def update(self, instance: ModelType, **kwargs) -> ModelType:
        """Update a record."""
        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        self.db.flush()
        return instance
    
    def update_by_id(self, id: int, **kwargs) -> Optional[ModelType]:
        """Update record by ID."""
        instance = self.get_by_id(id)
        if instance:
            return self.update(instance, **kwargs)
        return None
    
    def delete(self, instance: ModelType, soft_delete: bool = True) -> bool:
        """Delete a record."""
        if soft_delete and hasattr(instance, 'is_active'):
            instance.is_active = False
            if hasattr(instance, 'deleted_at'):
                instance.deleted_at = datetime.utcnow()
            self.db.flush()
            return True
        else:
            self.db.delete(instance)
            self.db.flush()
            return True
    
    def delete_by_id(self, id: int, soft_delete: bool = True) -> bool:
        """Delete record by ID."""
        instance = self.get_by_id(id)
        if instance:
            return self.delete(instance, soft_delete)
        return False
    
    def delete_bulk(self, ids: List[int], soft_delete: bool = True) -> int:
        """Delete multiple records."""
        query = self.db.query(self.model).filter(self.model.id.in_(ids))
        if soft_delete and hasattr(self.model, 'is_active'):
            count = query.update(
                {
                    "is_active": False,
                    "deleted_at": datetime.utcnow()
                },
                synchronize_session=False
            )
            return count
        else:
            count = query.delete(synchronize_session=False)
            return count
    
    def count(self, **filters) -> int:
        """Count records with filters."""
        query = self.db.query(self.model)
        for key, value in filters.items():
            if value is not None:
                query = query.filter(getattr(self.model, key) == value)
        return query.count()
    
    def exists(self, **filters) -> bool:
        """Check if record exists."""
        return self.count(**filters) > 0
    
    def get_or_create(self, defaults: Dict[str, Any] = None, **kwargs) -> tuple:
        """Get or create a record."""
        instance = self.get_by_fields(**kwargs)
        if instance:
            return instance, False
        create_data = {**kwargs}
        if defaults:
            create_data.update(defaults)
        return self.create(**create_data), True
    
    def bulk_upsert(self, items: List[Dict[str, Any]], unique_fields: List[str]) -> List[ModelType]:
        """
        Bulk upsert - update if exists, create if not.
        """
        results = []
        for item in items:
            filters = {field: item.get(field) for field in unique_fields}
            existing = self.get_by_fields(**filters)
            
            if existing:
                updated = self.update(existing, **item)
                results.append(updated)
            else:
                created = self.create(**item)
                results.append(created)
        
        return results
    
    def get_paginated(
        self,
        page: int = 1,
        page_size: int = 20,
        order_by: Optional[str] = None,
        order_desc: bool = True,
        **filters
    ) -> Dict[str, Any]:
        """
        Get paginated results.
        """
        skip = (page - 1) * page_size
        total = self.count(**filters)
        items = self.get_all(skip=skip, limit=page_size, order_by=order_by, order_desc=order_desc, **filters)
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if total > 0 else 0
        }
    
    def get_recent(self, limit: int = 10, **filters) -> List[ModelType]:
        """Get recent records."""
        return self.get_all(
            skip=0,
            limit=limit,
            order_by="created_at",
            order_desc=True,
            **filters
        )
    
    def get_stats(self, group_by: str, **filters) -> List[Dict[str, Any]]:
        """
        Get statistics grouped by field.
        """
        query = self.db.query(
            getattr(self.model, group_by),
            func.count(self.model.id).label("count")
        )
        
        for key, value in filters.items():
            if value is not None:
                query = query.filter(getattr(self.model, key) == value)
        
        results = query.group_by(getattr(self.model, group_by)).all()
        
        return [
            {
                "group": result[0],
                "count": result[1]
            }
            for result in results
        ]