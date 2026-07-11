# ============================================================
# app/repositories/search/__init__.py
# ============================================================
#
# Repository layer for the name/email search feature. Each repository
# here is responsible ONLY for database queries, filtering, and
# hydration - no business logic, no similarity scoring, no response
# formatting. Every query reads live from the database (no cache table,
# no embedding table), so a newly-inserted record is searchable
# immediately with zero manual refresh/reindex step.

from app.repositories.search.student_search_repository import StudentSearchRepository
from app.repositories.search.teacher_search_repository import TeacherSearchRepository

__all__ = ["StudentSearchRepository", "TeacherSearchRepository"]
