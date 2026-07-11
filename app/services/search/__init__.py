# ============================================================
# app/services/search/__init__.py
# ============================================================
#
# Orchestration layer for the name/email search feature. Each
# *_search_service.py: validates input (app/validators), queries its
# repository (app/repositories/search), scores candidates via the
# similarity engine (app/helpers/search), merges/ranks the results
# (same package), and returns plain result objects for the router to
# format into the API response. Services never execute raw SQL
# themselves - that's the repository's job.

from app.services.search.student_search_service import StudentSearchService, StudentSearchHit
from app.services.search.teacher_search_service import TeacherSearchService, TeacherSearchHit

__all__ = [
    "StudentSearchService",
    "StudentSearchHit",
    "TeacherSearchService",
    "TeacherSearchHit",
]
