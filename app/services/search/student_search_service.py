# ============================================================
# app/services/search/student_search_service.py
# ============================================================
#
# Orchestration ONLY - no raw SQL (that's StudentSearchRepository's job)
# and no similarity math (that's app/helpers/search's job). This module
# wires those two together for the Student entity:
#
#   validate query -> exact-match pass -> fuzzy pass -> rank/merge
#   -> hydrate full records -> return plain StudentSearchHit objects
#
# Always reads live from the database - there is no cache/embedding
# table to go stale, so a student created a second ago is searchable
# immediately.
#
# Teacher/Subject/Exam search follow the exact same shape (their own
# *_search_service.py using the same app/helpers/search + a dedicated
# repository) - see app/services/search/teacher_search_service.py for
# the next entity built this way.


from sqlalchemy.orm import Session, joinedload

from app.helpers.cache import search_cache
from app.helpers.search import (
    DEFAULT_RESULT_LIMIT,
    EMAIL_FUZZY_MIN_SCORE,
    FUZZY_CANDIDATE_POOL,
    QueryType,
    RawHit,
    normalize_text,
    rank_and_merge,
    rank_candidates,
)
from app.model import StudentClass, StudentProfile
from app.repositories.search import StudentSearchRepository
from app.validators import SearchQueryValidator

ENTITY_TYPE = "student"


class StudentSearchHit:
    """Plain result container handed to the router/schema layer."""

    def __init__(
        self,
        *,
        student,
        student_class,
        confidence,
        confidence_label,
        match_type,
        matched_field,
        signals,
    ) -> None:
        self.student = student
        self.student_class = student_class
        self.confidence = confidence
        self.confidence_label = confidence_label
        self.match_type = match_type
        self.matched_field = matched_field
        self.signals = signals


class StudentSearchService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = StudentSearchRepository(db)

    def search(
        self,
        raw_query: str,
        *,
        limit: int = DEFAULT_RESULT_LIMIT,
    ) -> list[StudentSearchHit]:
        """Always returns a ranked list of candidates - never auto-resolves
        a single "best" match, since names are never assumed unique. The
        caller (an admin/teacher picking the right student) makes the
        final selection using the returned student_id.
        """
        validated = SearchQueryValidator.validate(raw_query)

        hits: list[RawHit] = []
        hits.extend(self._exact_hits(validated.normalized, validated.cleaned))

        if validated.query_type == QueryType.EMAIL:
            # Query is shaped like an email - fuzzy-match against emails
            # only (tolerates a typo like "gmial.com"), skip the
            # name/code pool so it isn't diluted by unrelated matches.
            hits.extend(self._fuzzy_email_hits(validated.cleaned))
        else:
            hits.extend(self._fuzzy_name_hits(validated.cleaned))

        ranked = rank_and_merge(hits, limit=limit)
        return self._hydrate(ranked)

    # ------------------------------------------------------------
    # Matchers
    # ------------------------------------------------------------

    def _exact_hits(self, normalized_query: str, raw_query: str) -> list[RawHit]:
        rows = self.repository.find_exact(normalized_query, raw_query)

        results = []
        for student in rows:
            matched_field = self._which_field_matched(student, normalized_query)
            results.append(
                RawHit(
                    entity_key=student.student_id,
                    score=100.0,
                    match_type="exact",
                    matched_field=matched_field,
                ),
            )
        return results

    @staticmethod
    def _which_field_matched(student: StudentProfile, normalized: str) -> str:
        if normalize_text(student.student_name or "") == normalized:
            return "student_name"
        if normalize_text(student.student_id or "") == normalized:
            return "student_id"
        if normalize_text(student.admission_number or "") == normalized:
            return "admission_number"
        if normalize_text(student.registration_number or "") == normalized:
            return "registration_number"
        if student.user and normalize_text(student.user.email or "") == normalized:
            return "email"
        return "phone"

    def _fuzzy_name_hits(self, raw_query: str) -> list[RawHit]:
        candidates = search_cache.cached(
            "student_fuzzy_name_pool",
            lambda: self.repository.get_fuzzy_name_pool(FUZZY_CANDIDATE_POOL),
        )
        matches = rank_candidates(raw_query, candidates)

        return [
            RawHit(
                entity_key=key,
                score=score,
                match_type="fuzzy",
                matched_field="profile_text",
            )
            for key, score in matches
        ]

    def _fuzzy_email_hits(self, raw_query: str) -> list[RawHit]:
        candidates = search_cache.cached(
            "student_fuzzy_email_pool",
            lambda: self.repository.get_fuzzy_email_pool(FUZZY_CANDIDATE_POOL),
        )
        matches = rank_candidates(
            raw_query,
            candidates,
            score_cutoff=EMAIL_FUZZY_MIN_SCORE,
        )

        return [
            RawHit(
                entity_key=key,
                score=score,
                match_type="fuzzy",
                matched_field="email",
            )
            for key, score in matches
        ]

    # ------------------------------------------------------------
    # Hydration
    # ------------------------------------------------------------

    def _hydrate(self, ranked) -> list[StudentSearchHit]:
        if not ranked:
            return []

        student_ids = [r.entity_key for r in ranked]
        students = self.repository.get_by_ids(student_ids)
        by_id = {s.student_id: s for s in students}

        student_classes = (
            self.db.query(StudentClass)
            .options(joinedload(StudentClass.classroom))
            .filter(StudentClass.student_id.in_(student_ids), StudentClass.is_active)
            .all()
        )
        class_map = {}
        for sc in student_classes:
            class_map[sc.student_id] = {"student_class": sc, "classroom": sc.classroom}

        hydrated = []
        for r in ranked:
            student = by_id.get(r.entity_key)
            if not student:
                continue
            info = class_map.get(
                r.entity_key,
                {"student_class": None, "classroom": None},
            )
            hydrated.append(
                StudentSearchHit(
                    student=student,
                    student_class=info["student_class"],
                    confidence=round(r.confidence, 2),
                    confidence_label=r.confidence_label,
                    match_type=r.match_type,
                    matched_field=r.matched_field,
                    signals=r.signals,
                ),
            )
        return hydrated

    # ------------------------------------------------------------
    # ID resolution helper - used by other endpoints that want to accept
    # either a raw student_id OR a search query and resolve to an ID.
    # ------------------------------------------------------------

    def resolve_single(self, student_id: str) -> StudentProfile | None:
        """Straight ID lookup - no search/ranking involved. Existing
        business logic elsewhere in the codebase keeps using this (or
        the repositories it already had) unchanged; this is only here so
        callers that just resolved an ID out of a search result list can
        hydrate it through the same repository.
        """
        return self.repository.get_by_id(student_id)
