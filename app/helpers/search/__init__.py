# ============================================================
# app/helpers/search/__init__.py
# ============================================================
#
# Public surface of the similarity layer. Every *_search_service.py
# imports ONLY from this package (never reaches into the individual
# modules directly) so the internal split between text_utils /
# similarity_engine / ranking_engine can change without breaking callers.
#
# This package has ZERO knowledge of SQLAlchemy, FastAPI, or any
# specific entity (Student/Teacher/...). It only knows how to:
#   1. normalize + classify raw text (text_utils)
#   2. score how well a query matches a candidate string (similarity_engine)
#   3. merge multiple raw signals for the same record into one ranked,
#      explainable result (ranking_engine)

from app.helpers.search.text_utils import (
    normalize_text,
    build_search_text,
    looks_like_email,
    QueryType,
    classify_query,
)
from app.helpers.search.similarity_engine import (
    FUZZY_MIN_SCORE,
    EMAIL_FUZZY_MIN_SCORE,
    FUZZY_CANDIDATE_POOL,
    rank_candidates,
)
from app.helpers.search.ranking_engine import (
    EXACT_MATCH_SCORE,
    FINAL_CONFIDENCE_FLOOR,
    DEFAULT_RESULT_LIMIT,
    MAX_RESULT_LIMIT,
    RawHit,
    RankedResult,
    confidence_label,
    rank_and_merge,
)

__all__ = [
    "normalize_text",
    "build_search_text",
    "looks_like_email",
    "QueryType",
    "classify_query",
    "FUZZY_MIN_SCORE",
    "EMAIL_FUZZY_MIN_SCORE",
    "FUZZY_CANDIDATE_POOL",
    "rank_candidates",
    "EXACT_MATCH_SCORE",
    "FINAL_CONFIDENCE_FLOOR",
    "DEFAULT_RESULT_LIMIT",
    "MAX_RESULT_LIMIT",
    "RawHit",
    "RankedResult",
    "confidence_label",
    "rank_and_merge",
]
