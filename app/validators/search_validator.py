# ============================================================
# app/validators/search_validator.py
# ============================================================
#
# Every search request passes through here BEFORE it reaches a
# repository or the similarity engine. Responsible for:
#   - empty / null / whitespace-only input
#   - control characters (non-printable input, e.g. pasted garbage)
#   - too-short / too-long input
#   - detecting (but NOT rejecting) malformed-email-shaped input, so the
#     service layer can degrade gracefully instead of hard-failing
#
# No database code, no similarity/ranking code here.

from dataclasses import dataclass

from app.core.exceptions import SearchValidationError
from app.helpers.search.text_utils import (
    QueryType,
    classify_query,
    is_valid_email_format,
    normalize_text,
)

MIN_QUERY_LENGTH = 1
MAX_QUERY_LENGTH = 100


@dataclass
class ValidatedQuery:
    raw: str  # exactly what the user typed, untouched
    cleaned: str  # whitespace-trimmed, control-chars stripped
    normalized: str  # lowercase/accent-stripped form (see text_utils.normalize_text)
    query_type: QueryType  # EMAIL | NAME_OR_CODE, auto-detected
    is_well_formed_email: bool  # only meaningful when query_type == EMAIL


class SearchQueryValidator:
    """Stateless validator - one static entrypoint, no DB/session needed."""

    @staticmethod
    def validate(raw_query: str) -> ValidatedQuery:
        if raw_query is None:
            raise SearchValidationError("Search query is required.")

        if not isinstance(raw_query, str):
            raise SearchValidationError("Search query must be text.")

        # Strip non-printable / control characters (keep normal spaces),
        # then collapse whitespace. Handles pasted garbage, zero-width
        # characters, stray newlines/tabs, etc. Unicode letters (accents,
        # non-Latin scripts) are explicitly preserved - this is a
        # control-character filter, not an ASCII filter.
        cleaned = "".join(
            ch for ch in raw_query if ch.isprintable() or ch.isspace()
        ).strip()
        cleaned = " ".join(cleaned.split())

        if len(cleaned) < MIN_QUERY_LENGTH:
            raise SearchValidationError("Search query cannot be empty.")

        if len(cleaned) > MAX_QUERY_LENGTH:
            raise SearchValidationError(
                f"Search query is too long (max {MAX_QUERY_LENGTH} characters)."
            )

        query_type = classify_query(cleaned)
        is_well_formed_email = (
            is_valid_email_format(cleaned) if query_type == QueryType.EMAIL else False
        )
        # Note: an email-SHAPED-but-malformed query (e.g. "a@@b") is not
        # rejected here - it's still searched as free text so a user with
        # a typo in their query still gets fuzzy name/code results
        # instead of a hard error. `is_well_formed_email` just tells the
        # service layer whether an exact-email lookup is worth attempting.

        return ValidatedQuery(
            raw=raw_query,
            cleaned=cleaned,
            normalized=normalize_text(cleaned),
            query_type=query_type,
            is_well_formed_email=is_well_formed_email,
        )
