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

from app.helpers.search.ranking_engine import (
    DEFAULT_RESULT_LIMIT,
    EXACT_MATCH_SCORE,
    FINAL_CONFIDENCE_FLOOR,
    MAX_RESULT_LIMIT,
    RankedResult,
    RawHit,
    confidence_label,
    rank_and_merge,
)
from app.helpers.search.similarity_engine import (
    EMAIL_FUZZY_MIN_SCORE,
    FUZZY_CANDIDATE_POOL,
    FUZZY_MIN_SCORE,
    rank_candidates,
)
from app.helpers.search.text_utils import (
    QueryType,
    build_search_text,
    classify_query,
    looks_like_email,
    normalize_text,
)

__all__ = [
    "DEFAULT_RESULT_LIMIT",
    "EMAIL_FUZZY_MIN_SCORE",
    "EXACT_MATCH_SCORE",
    "FINAL_CONFIDENCE_FLOOR",
    "FUZZY_CANDIDATE_POOL",
    "FUZZY_MIN_SCORE",
    "MAX_RESULT_LIMIT",
    "QueryType",
    "RankedResult",
    "RawHit",
    "build_search_text",
    "classify_query",
    "confidence_label",
    "looks_like_email",
    "normalize_text",
    "rank_and_merge",
    "rank_candidates",
]
