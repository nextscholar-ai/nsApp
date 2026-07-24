# ============================================================
# app/services/search/teacher_search_service.py
# ============================================================
#
# Same shape as StudentSearchService - see that module's docstring for
# the overall pipeline. Kept separate (not a shared generic class) so
# entity-specific field names stay explicit and easy to follow; the
# actually-shared logic (normalization, fuzzy scoring, ranking) already
# lives in one place: app/helpers/search.


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
from app.model import TeacherProfile, TeacherSubject
from app.repositories.search import TeacherSearchRepository
from app.validators import SearchQueryValidator

ENTITY_TYPE = "teacher"


class TeacherSearchHit:
    def __init__(
        self,
        *,
        teacher,
        subjects,
        class_teacher_of,
        confidence,
        confidence_label,
        match_type,
        matched_field,
        signals,
    ) -> None:
        self.teacher = teacher
        self.subjects = subjects
        self.class_teacher_of = class_teacher_of
        self.confidence = confidence
        self.confidence_label = confidence_label
        self.match_type = match_type
        self.matched_field = matched_field
        self.signals = signals


class TeacherSearchService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = TeacherSearchRepository(db)

    def search(
        self,
        raw_query: str,
        *,
        limit: int = DEFAULT_RESULT_LIMIT,
    ) -> list[TeacherSearchHit]:
        validated = SearchQueryValidator.validate(raw_query)

        hits: list[RawHit] = []
        hits.extend(self._exact_hits(validated.normalized, validated.cleaned))

        if validated.query_type == QueryType.EMAIL:
            hits.extend(self._fuzzy_email_hits(validated.cleaned))
        else:
            hits.extend(self._fuzzy_name_hits(validated.cleaned))

        ranked = rank_and_merge(hits, limit=limit)
        return self._hydrate(ranked)

    def _exact_hits(self, normalized_query: str, raw_query: str) -> list[RawHit]:
        rows = self.repository.find_exact(normalized_query, raw_query)

        results = []
        for teacher in rows:
            matched_field = self._which_field_matched(teacher, normalized_query)
            results.append(
                RawHit(
                    entity_key=teacher.teacher_id,
                    score=100.0,
                    match_type="exact",
                    matched_field=matched_field,
                ),
            )
        return results

    @staticmethod
    def _which_field_matched(teacher: TeacherProfile, normalized: str) -> str:
        if normalize_text(teacher.teacher_name or "") == normalized:
            return "teacher_name"
        if normalize_text(teacher.teacher_id or "") == normalized:
            return "teacher_id"
        if normalize_text(teacher.employee_code or "") == normalized:
            return "employee_code"
        if teacher.user and normalize_text(teacher.user.email or "") == normalized:
            return "email"
        return "phone"

    def _fuzzy_name_hits(self, raw_query: str) -> list[RawHit]:
        candidates = search_cache.cached(
            "teacher_fuzzy_name_pool",
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
            "teacher_fuzzy_email_pool",
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

    def _hydrate(self, ranked) -> list[TeacherSearchHit]:
        if not ranked:
            return []

        teacher_ids = [r.entity_key for r in ranked]
        teachers = self.repository.get_by_ids(teacher_ids)
        by_id = {t.teacher_id: t for t in teachers}

        teacher_subjects = (
            self.db.query(TeacherSubject)
            .options(joinedload(TeacherSubject.subject))
            .filter(
                TeacherSubject.teacher_id.in_(teacher_ids),
                TeacherSubject.is_active,
            )
            .all()
        )
        subject_map = {}
        for ts in teacher_subjects:
            subject_map.setdefault(ts.teacher_id, []).append(
                ts.subject.subject_name if ts.subject else "Unknown",
            )

        from app.model import ClassRoom

        class_teacher_map = {}
        class_teacher_rows = (
            self.db.query(ClassRoom)
            .filter(ClassRoom.class_teacher_id.in_(teacher_ids), ClassRoom.is_active)
            .all()
        )
        for ct in class_teacher_rows:
            class_teacher_map[ct.class_teacher_id] = ct.display_name

        hydrated = []
        for r in ranked:
            teacher = by_id.get(r.entity_key)
            if not teacher:
                continue
            hydrated.append(
                TeacherSearchHit(
                    teacher=teacher,
                    subjects=subject_map.get(r.entity_key, []),
                    class_teacher_of=class_teacher_map.get(r.entity_key),
                    confidence=round(r.confidence, 2),
                    confidence_label=r.confidence_label,
                    match_type=r.match_type,
                    matched_field=r.matched_field,
                    signals=r.signals,
                ),
            )
        return hydrated

    def resolve_single(self, teacher_id: str) -> TeacherProfile | None:
        return self.repository.get_by_id(teacher_id)
