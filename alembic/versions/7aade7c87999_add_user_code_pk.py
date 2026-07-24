"""add_user_code_pk

Revision ID: 7aade7c87999
Revises: 15826d464da8
Create Date: 2026-07-24 16:43:55.392210

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.helpers.code_generators import generate_user_code

revision: str = '7aade7c87999'
down_revision: Union[str, Sequence[str], None] = '15826d464da8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def xfk(connection, table, col, ref_table, ref_col, ref_pk="id"):
    new = col + "_new"
    op.add_column(table, sa.Column(new, sa.String(30), nullable=True))
    connection.execute(sa.text(f"""
        UPDATE {table}
        SET {new} = (
            SELECT {ref_col} FROM {ref_table}
            WHERE {ref_table}.{ref_pk}::text = {table}.{col}::text
        )
        WHERE {table}.{col} IS NOT NULL
    """))
    op.drop_column(table, col)
    op.execute(f'ALTER TABLE {table} RENAME COLUMN {new} TO {col}')
    connection.execute(sa.text(f"ALTER TABLE {table} ALTER COLUMN {col} TYPE VARCHAR(30)"))


def cast_int(table, col, nullable, size="30"):
    op.execute(
        f'ALTER TABLE {table} ALTER COLUMN {col} TYPE VARCHAR({size}) '
        f'USING {col}::varchar({size})'
    )
    if not nullable:
        op.execute(f'ALTER TABLE {table} ALTER COLUMN {col} SET NOT NULL')


def add_code_column(table, col_name, size=30):
    try:
        op.add_column(table, sa.Column(col_name, sa.String(size), nullable=True))
    except Exception:
        pass


def set_code_value(connection, table, code_col):
    row_count = connection.execute(sa.text(f'SELECT COUNT(*) FROM {table}')).fetchone()[0]
    if row_count == 0:
        return
    codes = {}
    rows = connection.execute(sa.text(f'SELECT id FROM {table}')).fetchall()
    for (rid,) in rows:
        codes[rid] = generate_user_code()
    for rid, code in codes.items():
        connection.execute(
            sa.text(f'UPDATE {table} SET {code_col} = :code WHERE id = :id'),
            {"code": code, "id": rid},
        )
    connection.execute(sa.text(f'ALTER TABLE {table} ALTER COLUMN {code_col} SET NOT NULL'))


def drop_id_column(table):
    try:
        op.drop_column(table, "id")
    except Exception:
        pass


def switch_pk(table, new_pk_col):
    try:
        op.drop_constraint(f"{table}_pkey", table, type_="primary")
    except Exception:
        pass
    op.create_primary_key(f"{table}_pkey", table, [new_pk_col])


def upgrade() -> None:
    connection = op.get_bind()

    # ----------------------------------------------------------------
    # Phase 0: Drop ALL FK constraints
    # ----------------------------------------------------------------
    rows = connection.execute(sa.text("""
        SELECT conrelid::regclass::text, conname
        FROM pg_constraint
        WHERE contype = 'f'
          AND conrelid::regclass::text IN (
            'academic_sessions','admin_profiles','assignments','assignment_results',
            'attachments','chat_messages','chat_rooms','class_subjects','class_timetable',
            'classroom','daily_class_students','daily_classes','exam_results','exams',
            'fees','notices','student_attendance','student_classes','student_id_cards',
            'student_promotion_history','study_materials','subjects','teacher_availability',
            'teacher_profiles','teacher_subjects','users','student_profiles',
            'zoom_recording_file','zoom_student_interaction','zoom_transcript'
          )
        ORDER BY conname
    """)).fetchall()

    fk_count = 0
    for tbl_raw, con_raw in rows:
        tbl = str(tbl_raw).strip('"')
        con = str(con_raw).strip()
        try:
            connection.execute(sa.text(f'ALTER TABLE "{tbl}" DROP CONSTRAINT "{con}"'))
            fk_count += 1
        except Exception:
            pass
    print(f"Dropped {fk_count} FK constraints")

    connection.execute(sa.text("SET session_replication_role = replica;"))

    try:
        # ----------------------------------------------------------------
        # Phase 1: Add user_code to users + populate
        # ----------------------------------------------------------------
        add_code_column("users", "user_code", 30)
        ids = connection.execute(sa.text("SELECT id FROM users")).fetchall()
        for (uid,) in ids:
            code = generate_user_code()
            connection.execute(
                sa.text("UPDATE users SET user_code = :code WHERE id = :id"),
                {"code": code, "id": uid},
            )
        connection.execute(sa.text("ALTER TABLE users ALTER COLUMN user_code SET NOT NULL"))

        # ----------------------------------------------------------------
        # Phase 2: Add _code columns to all tables that need them
        # ----------------------------------------------------------------
        code_additions = [
            ("assignment_results", "assignment_result_code"),
            ("assignments", "assignment_code"),
            ("chat_messages", "chat_message_code"),
            ("chat_rooms", "chat_room_code"),
            ("class_subjects", "class_subject_code"),
            ("class_timetable", "timetable_code"),
            ("daily_class_students", "daily_class_student_code"),
            ("daily_classes", "daily_class_code"),
            ("exam_results", "exam_result_code"),
            ("exams", "exam_code"),
            ("fees", "fee_code"),
            ("notices", "notice_code"),
            ("student_attendance", "attendance_code"),
            ("student_classes", "student_class_code"),
            ("student_id_cards", "id_card_code"),
            ("student_promotion_history", "promotion_code"),
            ("study_materials", "material_code"),
            ("teacher_availability", "availability_code"),
            ("teacher_subjects", "teacher_subject_code"),
        ]
        for tbl, col in code_additions:
            add_code_column(tbl, col)

        # ----------------------------------------------------------------
        # Phase 3: Populate _code for tables with data
        # ----------------------------------------------------------------
        set_code_value(connection, "student_classes", "student_class_code")

        # ----------------------------------------------------------------
        # Phase 4: Transform FK columns (xfk)
        # ----------------------------------------------------------------
        # users FKs
        for tbl, col in [
            ("admin_profiles", "user_id"),
            ("student_profiles", "user_id"),
            ("teacher_profiles", "user_id"),
            ("subjects", "created_by"),
            ("subjects", "updated_by"),
            ("classroom", "created_by"),
            ("classroom", "updated_by"),
            ("class_subjects", "created_by"),
            ("class_subjects", "updated_by"),
            ("student_promotion_history", "promoted_by_user_id"),
            ("notices", "created_by"),
            ("notices", "deleted_by"),
            ("notices", "updated_by"),
            ("fees", "created_by"),
            ("fees", "deleted_by"),
            ("fees", "updated_by"),
            ("assignments", "created_by"),
            ("assignments", "deleted_by"),
            ("assignments", "updated_by"),
            ("assignments", "uploaded_by"),
            ("study_materials", "uploaded_by"),
            ("exams", "created_by"),
            ("exams", "deleted_by"),
            ("exams", "updated_by"),
            ("assignment_results", "checked_by"),
            ("exam_results", "checked_by"),
            ("chat_messages", "sender_id"),
            ("daily_class_students", "marked_by"),
            ("academic_sessions", "created_by"),
            ("academic_sessions", "updated_by"),
            ("attachments", "created_by"),
            ("attachments", "updated_by"),
            ("student_profiles", "created_by"),
            ("student_profiles", "updated_by"),
            ("teacher_profiles", "created_by"),
            ("teacher_profiles", "updated_by"),
            ("admin_profiles", "created_by"),
            ("admin_profiles", "updated_by"),
        ]:
            xfk(connection, tbl, col, "users", "user_code", "id")

        for col in ("created_by", "updated_by", "deleted_by"):
            xfk(connection, "users", col, "users", "user_code", "id")

        # academic_sessions FKs
        for tbl, col in [
            ("assignments", "academic_sessions_id"),
            ("chat_rooms", "academic_sessions_id"),
            ("class_subjects", "academic_sessions_id"),
            ("class_timetable", "academic_sessions_id"),
            ("classroom", "academic_sessions_id"),
            ("daily_classes", "academic_sessions_id"),
            ("exams", "academic_sessions_id"),
            ("fees", "academic_sessions_id"),
            ("notices", "academic_sessions_id"),
            ("student_classes", "academic_sessions_id"),
            ("student_id_cards", "academic_sessions_id"),
            ("student_promotion_history", "from_session_id"),
            ("student_promotion_history", "to_session_id"),
            ("study_materials", "academic_sessions_id"),
            ("teacher_availability", "academic_sessions_id"),
            ("teacher_subjects", "academic_sessions_id"),
        ]:
            xfk(connection, tbl, col, "academic_sessions", "session_code", "id")

        # classroom FKs
        for tbl, col in [
            ("assignments", "classroom_id"),
            ("class_subjects", "classroom_id"),
            ("class_timetable", "classroom_id"),
            ("daily_classes", "classroom_id"),
            ("exams", "classroom_id"),
            ("notices", "classroom_id"),
            ("student_classes", "classroom_id"),
            ("student_promotion_history", "from_classroom_id"),
            ("student_promotion_history", "to_classroom_id"),
            ("study_materials", "classroom_id"),
            ("teacher_subjects", "classroom_id"),
        ]:
            xfk(connection, tbl, col, "classroom", "class_code", "id")

        # subjects FKs
        for tbl, col in [
            ("class_subjects", "subject_id"),
            ("teacher_subjects", "subject_id"),
        ]:
            xfk(connection, tbl, col, "subjects", "subject_code", "id")

        # class_subjects FKs
        for tbl, col in [
            ("assignments", "class_subject_id"),
            ("class_timetable", "class_subject_id"),
            ("daily_classes", "class_subject_id"),
            ("exams", "class_subject_id"),
            ("study_materials", "class_subject_id"),
            ("teacher_subjects", "class_subject_id"),
        ]:
            xfk(connection, tbl, col, "class_subjects", "class_subject_code", "id")

        # teacher_subjects FKs
        for tbl, col in [
            ("assignments", "teacher_subject_id"),
            ("class_timetable", "teacher_subject_id"),
            ("daily_classes", "teacher_subject_id"),
            ("exams", "teacher_subject_id"),
            ("study_materials", "teacher_subject_id"),
            ("teacher_availability", "teacher_subject_id"),
            ("chat_rooms", "teacher_subject_id"),
        ]:
            xfk(connection, tbl, col, "teacher_subjects", "teacher_subject_code", "id")

        # assignments FK
        for tbl, col in [
            ("assignment_results", "assignment_id"),
        ]:
            xfk(connection, tbl, col, "assignments", "assignment_code", "id")

        # student_classes FKs
        for tbl, col in [
            ("assignment_results", "student_class_id"),
            ("exam_results", "student_class_id"),
            ("fees", "student_class_id"),
            ("student_attendance", "student_class_id"),
            ("daily_class_students", "student_class_id"),
            ("chat_rooms", "student_class_id"),
        ]:
            xfk(connection, tbl, col, "student_classes", "student_class_code", "id")

        # chat_rooms FK
        for tbl, col in [
            ("chat_messages", "chat_room_id"),
        ]:
            xfk(connection, tbl, col, "chat_rooms", "chat_room_code", "id")

        # daily_classes FKs
        for tbl, col in [
            ("daily_class_students", "daily_class_id"),
        ]:
            xfk(connection, tbl, col, "daily_classes", "daily_class_code", "id")

        # class_timetable FK
        for tbl, col in [
            ("daily_classes", "timetable_id"),
        ]:
            xfk(connection, tbl, col, "class_timetable", "timetable_code", "id")

        # exams FK
        for tbl, col in [
            ("exam_results", "exam_id"),
        ]:
            xfk(connection, tbl, col, "exams", "exam_code", "id")

        # week_day_id / time_slot_id (empty tables, just cast)
        for tbl, col, sz, n in [
            ("class_timetable", "week_day_id", 3, False),
            ("class_timetable", "time_slot_id", 10, False),
            ("teacher_availability", "week_day_id", 3, False),
            ("teacher_availability", "time_slot_id", 10, False),
        ]:
            cast_int(tbl, col, n, str(sz))

        # attachments.entity_id (polymorphic FK, keep as varchar)
        cast_int("attachments", "entity_id", False)

        # ----------------------------------------------------------------
        # Phase 5: Switch PK from id to _code, drop id
        # ----------------------------------------------------------------
        pk_switches = [
            ("users", "user_code"),
            ("academic_sessions", "session_code"),
            ("assignment_results", "assignment_result_code"),
            ("assignments", "assignment_code"),
            ("attachments", "attachment_code"),
            ("chat_messages", "chat_message_code"),
            ("chat_rooms", "chat_room_code"),
            ("class_subjects", "class_subject_code"),
            ("class_timetable", "timetable_code"),
            ("classroom", "class_code"),
            ("daily_class_students", "daily_class_student_code"),
            ("daily_classes", "daily_class_code"),
            ("exam_results", "exam_result_code"),
            ("exams", "exam_code"),
            ("fees", "fee_code"),
            ("notices", "notice_code"),
            ("student_attendance", "attendance_code"),
            ("student_classes", "student_class_code"),
            ("student_id_cards", "id_card_code"),
            ("student_promotion_history", "promotion_code"),
            ("study_materials", "material_code"),
            ("subjects", "subject_code"),
            ("teacher_availability", "availability_code"),
            ("teacher_subjects", "teacher_subject_code"),
            ("time_slots", "slot_code"),
            ("week_days", "day_code"),
        ]
        for tbl, code_col in pk_switches:
            switch_pk(tbl, code_col)
            drop_id_column(tbl)

        # ----------------------------------------------------------------
        # Phase 6: Cleanup
        # ----------------------------------------------------------------
        try:
            op.drop_table("search_embeddings")
        except Exception:
            pass

        for sql in [
            "DROP INDEX IF EXISTS ix_academic_sessions_session_code",
            "DROP INDEX IF EXISTS ix_attachments_attachment_code",
            "DROP INDEX IF EXISTS ix_chat_rooms_chat_room_id",
            "DROP INDEX IF EXISTS ix_class_timetable_timetable_id",
            "DROP INDEX IF EXISTS ix_exams_exam_id",
            "DROP INDEX IF EXISTS ix_fees_fee_id",
            "DROP INDEX IF EXISTS ix_notices_notice_id",
            "DROP INDEX IF EXISTS ix_student_classes_id",
            "DROP INDEX IF EXISTS ix_student_id_cards_id",
            "DROP INDEX IF EXISTS ix_student_promotion_history_id",
            "DROP INDEX IF EXISTS ix_study_materials_material_id",
            "DROP INDEX IF EXISTS ix_subjects_subject_code",
            "DROP INDEX IF EXISTS ix_teacher_availability_availability_id",
            "DROP INDEX IF EXISTS ix_assignments_assignment_id",
            "DROP INDEX IF EXISTS ix_daily_classes_daily_class_id",
            "DROP INDEX IF EXISTS ix_teacher_subjects_id",
            "ALTER TABLE admin_profiles DROP CONSTRAINT IF EXISTS uq_admin_user",
        ]:
            try:
                connection.execute(sa.text(sql))
            except Exception:
                pass

    except Exception as e:
        connection.execute(sa.text("SET session_replication_role = DEFAULT;"))
        raise e

    connection.execute(sa.text("SET session_replication_role = DEFAULT;"))

    # ----------------------------------------------------------------
    # Phase 7: Recreate foreign keys
    # ----------------------------------------------------------------
    all_fks = [
        ("admin_profiles", "admin_profiles_user_id_fkey", "user_id", "users", "user_code", {"ondelete": "CASCADE"}),
        ("student_profiles", "student_profiles_user_id_fkey", "user_id", "users", "user_code", {}),
        ("teacher_profiles", "teacher_profiles_user_id_fkey", "user_id", "users", "user_code", {}),
        ("subjects", "subjects_created_by_fkey", "created_by", "users", "user_code", {"ondelete": "SET NULL"}),
        ("subjects", "subjects_updated_by_fkey", "updated_by", "users", "user_code", {"ondelete": "SET NULL"}),
        ("classroom", "classroom_created_by_fkey", "created_by", "users", "user_code", {"ondelete": "SET NULL"}),
        ("classroom", "classroom_updated_by_fkey", "updated_by", "users", "user_code", {"ondelete": "SET NULL"}),
        ("classroom", "classroom_class_teacher_id_fkey", "class_teacher_id", "teacher_profiles", "teacher_id", {}),
        ("class_subjects", "class_subjects_created_by_fkey", "created_by", "users", "user_code", {"ondelete": "SET NULL"}),
        ("class_subjects", "class_subjects_updated_by_fkey", "updated_by", "users", "user_code", {"ondelete": "SET NULL"}),
        ("student_promotion_history", "student_promotion_history_promoted_by_user_id_fkey", "promoted_by_user_id", "users", "user_code", {}),
        ("notices", "notices_created_by_fkey", "created_by", "users", "user_code", {}),
        ("notices", "notices_deleted_by_fkey", "deleted_by", "users", "user_code", {}),
        ("notices", "notices_updated_by_fkey", "updated_by", "users", "user_code", {}),
        ("fees", "fees_created_by_fkey", "created_by", "users", "user_code", {}),
        ("fees", "fees_deleted_by_fkey", "deleted_by", "users", "user_code", {}),
        ("fees", "fees_updated_by_fkey", "updated_by", "users", "user_code", {}),
        ("assignments", "assignments_created_by_fkey", "created_by", "users", "user_code", {}),
        ("assignments", "assignments_deleted_by_fkey", "deleted_by", "users", "user_code", {}),
        ("assignments", "assignments_updated_by_fkey", "updated_by", "users", "user_code", {}),
        ("assignments", "assignments_uploaded_by_fkey", "uploaded_by", "users", "user_code", {}),
        ("study_materials", "study_materials_uploaded_by_fkey", "uploaded_by", "users", "user_code", {}),
        ("exams", "exams_created_by_fkey", "created_by", "users", "user_code", {}),
        ("exams", "exams_deleted_by_fkey", "deleted_by", "users", "user_code", {}),
        ("exams", "exams_updated_by_fkey", "updated_by", "users", "user_code", {}),
        ("assignment_results", "assignment_results_checked_by_fkey", "checked_by", "users", "user_code", {}),
        ("exam_results", "exam_results_checked_by_fkey", "checked_by", "users", "user_code", {}),
        ("chat_messages", "chat_messages_sender_id_fkey", "sender_id", "users", "user_code", {}),
        ("daily_class_students", "daily_class_students_marked_by_fkey", "marked_by", "users", "user_code", {}),
        ("academic_sessions", "academic_sessions_created_by_fkey", "created_by", "users", "user_code", {"ondelete": "SET NULL"}),
        ("academic_sessions", "academic_sessions_updated_by_fkey", "updated_by", "users", "user_code", {"ondelete": "SET NULL"}),
        ("attachments", "attachments_created_by_fkey", "created_by", "users", "user_code", {"ondelete": "SET NULL"}),
        ("attachments", "attachments_updated_by_fkey", "updated_by", "users", "user_code", {"ondelete": "SET NULL"}),
        ("student_profiles", "student_profiles_created_by_fkey", "created_by", "users", "user_code", {"ondelete": "SET NULL"}),
        ("student_profiles", "student_profiles_updated_by_fkey", "updated_by", "users", "user_code", {"ondelete": "SET NULL"}),
        ("teacher_profiles", "teacher_profiles_created_by_fkey", "created_by", "users", "user_code", {"ondelete": "SET NULL"}),
        ("teacher_profiles", "teacher_profiles_updated_by_fkey", "updated_by", "users", "user_code", {"ondelete": "SET NULL"}),
        ("admin_profiles", "admin_profiles_created_by_fkey", "created_by", "users", "user_code", {"ondelete": "SET NULL"}),
        ("admin_profiles", "admin_profiles_updated_by_fkey", "updated_by", "users", "user_code", {"ondelete": "SET NULL"}),
        ("assignments", "assignments_academic_sessions_id_fkey", "academic_sessions_id", "academic_sessions", "session_code", {}),
        ("chat_rooms", "chat_rooms_academic_sessions_id_fkey", "academic_sessions_id", "academic_sessions", "session_code", {}),
        ("class_subjects", "class_subjects_academic_sessions_id_fkey", "academic_sessions_id", "academic_sessions", "session_code", {"ondelete": "CASCADE"}),
        ("class_timetable", "class_timetable_academic_sessions_id_fkey", "academic_sessions_id", "academic_sessions", "session_code", {}),
        ("classroom", "classroom_academic_sessions_id_fkey", "academic_sessions_id", "academic_sessions", "session_code", {"ondelete": "RESTRICT"}),
        ("daily_classes", "daily_classes_academic_sessions_id_fkey", "academic_sessions_id", "academic_sessions", "session_code", {}),
        ("exams", "exams_academic_sessions_id_fkey", "academic_sessions_id", "academic_sessions", "session_code", {}),
        ("fees", "fees_academic_sessions_id_fkey", "academic_sessions_id", "academic_sessions", "session_code", {}),
        ("notices", "notices_academic_sessions_id_fkey", "academic_sessions_id", "academic_sessions", "session_code", {}),
        ("student_classes", "student_classes_academic_sessions_id_fkey", "academic_sessions_id", "academic_sessions", "session_code", {"ondelete": "RESTRICT"}),
        ("student_id_cards", "student_id_cards_academic_sessions_id_fkey", "academic_sessions_id", "academic_sessions", "session_code", {"ondelete": "RESTRICT"}),
        ("student_promotion_history", "student_promotion_history_from_session_id_fkey", "from_session_id", "academic_sessions", "session_code", {}),
        ("student_promotion_history", "student_promotion_history_to_session_id_fkey", "to_session_id", "academic_sessions", "session_code", {}),
        ("study_materials", "study_materials_academic_sessions_id_fkey", "academic_sessions_id", "academic_sessions", "session_code", {}),
        ("teacher_availability", "teacher_availability_academic_sessions_id_fkey", "academic_sessions_id", "academic_sessions", "session_code", {}),
        ("teacher_subjects", "teacher_subjects_academic_sessions_id_fkey", "academic_sessions_id", "academic_sessions", "session_code", {"ondelete": "CASCADE"}),
        ("assignments", "assignments_classroom_id_fkey", "classroom_id", "classroom", "class_code", {}),
        ("class_subjects", "class_subjects_classroom_id_fkey", "classroom_id", "classroom", "class_code", {"ondelete": "CASCADE"}),
        ("class_timetable", "class_timetable_classroom_id_fkey", "classroom_id", "classroom", "class_code", {}),
        ("daily_classes", "daily_classes_classroom_id_fkey", "classroom_id", "classroom", "class_code", {}),
        ("exams", "exams_classroom_id_fkey", "classroom_id", "classroom", "class_code", {}),
        ("notices", "notices_classroom_id_fkey", "classroom_id", "classroom", "class_code", {}),
        ("student_classes", "student_classes_classroom_id_fkey", "classroom_id", "classroom", "class_code", {"ondelete": "RESTRICT"}),
        ("student_promotion_history", "student_promotion_history_from_classroom_id_fkey", "from_classroom_id", "classroom", "class_code", {}),
        ("student_promotion_history", "student_promotion_history_to_classroom_id_fkey", "to_classroom_id", "classroom", "class_code", {}),
        ("study_materials", "study_materials_classroom_id_fkey", "classroom_id", "classroom", "class_code", {}),
        ("teacher_subjects", "teacher_subjects_classroom_id_fkey", "classroom_id", "classroom", "class_code", {"ondelete": "CASCADE"}),
        ("class_timetable", "class_timetable_week_day_id_fkey", "week_day_id", "week_days", "day_code", {}),
        ("class_timetable", "class_timetable_time_slot_id_fkey", "time_slot_id", "time_slots", "slot_code", {}),
        ("class_timetable", "class_timetable_teacher_subject_id_fkey", "teacher_subject_id", "teacher_subjects", "teacher_subject_code", {}),
        ("class_timetable", "class_timetable_class_subject_id_fkey", "class_subject_id", "class_subjects", "class_subject_code", {}),
        ("teacher_availability", "teacher_availability_teacher_subject_id_fkey", "teacher_subject_id", "teacher_subjects", "teacher_subject_code", {}),
        ("teacher_availability", "teacher_availability_time_slot_id_fkey", "time_slot_id", "time_slots", "slot_code", {}),
        ("teacher_availability", "teacher_availability_week_day_id_fkey", "week_day_id", "week_days", "day_code", {}),
        ("daily_classes", "daily_classes_class_subject_id_fkey", "class_subject_id", "class_subjects", "class_subject_code", {}),
        ("daily_classes", "daily_classes_teacher_subject_id_fkey", "teacher_subject_id", "teacher_subjects", "teacher_subject_code", {}),
        ("daily_classes", "daily_classes_timetable_id_fkey", "timetable_id", "class_timetable", "timetable_code", {}),
        ("exams", "exams_class_subject_id_fkey", "class_subject_id", "class_subjects", "class_subject_code", {}),
        ("exams", "exams_teacher_subject_id_fkey", "teacher_subject_id", "teacher_subjects", "teacher_subject_code", {}),
        ("assignments", "assignments_class_subject_id_fkey", "class_subject_id", "class_subjects", "class_subject_code", {}),
        ("assignments", "assignments_teacher_subject_id_fkey", "teacher_subject_id", "teacher_subjects", "teacher_subject_code", {}),
        ("chat_rooms", "chat_rooms_teacher_subject_id_fkey", "teacher_subject_id", "teacher_subjects", "teacher_subject_code", {}),
        ("chat_rooms", "chat_rooms_student_class_id_fkey", "student_class_id", "student_classes", "student_class_code", {}),
        ("study_materials", "study_materials_class_subject_id_fkey", "class_subject_id", "class_subjects", "class_subject_code", {}),
        ("study_materials", "study_materials_teacher_subject_id_fkey", "teacher_subject_id", "teacher_subjects", "teacher_subject_code", {}),
        ("teacher_subjects", "teacher_subjects_class_subject_id_fkey", "class_subject_id", "class_subjects", "class_subject_code", {"ondelete": "CASCADE"}),
        ("teacher_subjects", "teacher_subjects_subject_id_fkey", "subject_id", "subjects", "subject_code", {"ondelete": "CASCADE"}),
        ("assignment_results", "assignment_results_assignment_id_fkey", "assignment_id", "assignments", "assignment_code", {}),
        ("assignment_results", "assignment_results_student_class_id_fkey", "student_class_id", "student_classes", "student_class_code", {}),
        ("exam_results", "exam_results_exam_id_fkey", "exam_id", "exams", "exam_code", {}),
        ("exam_results", "exam_results_student_class_id_fkey", "student_class_id", "student_classes", "student_class_code", {}),
        ("fees", "fees_student_class_id_fkey", "student_class_id", "student_classes", "student_class_code", {}),
        ("student_attendance", "student_attendance_student_class_id_fkey", "student_class_id", "student_classes", "student_class_code", {}),
        ("daily_class_students", "daily_class_students_student_class_id_fkey", "student_class_id", "student_classes", "student_class_code", {}),
        ("daily_class_students", "daily_class_students_daily_class_id_fkey", "daily_class_id", "daily_classes", "daily_class_code", {}),
        ("chat_messages", "chat_messages_chat_room_id_fkey", "chat_room_id", "chat_rooms", "chat_room_code", {}),
        # Zoom FKs (were dropped, need recreate)
        ("zoom_student_interaction", "zoom_student_interaction_zoom_file_id_fkey", "zoom_file_id", "zoom_recording_file", "id", {}),
        ("zoom_transcript", "zoom_transcript_zoom_file_id_fkey", "zoom_file_id", "zoom_recording_file", "id", {}),
        ("zoom_recording_file", "zoom_recording_file_meeting_uuid_fkey", "meeting_uuid", "zoom_meeting", "uuid", {}),
        # Existing VARCHAR FKs
        ("student_profiles", "student_profiles_student_id_fkey", "student_id", "users", "student_id", {}),
        ("teacher_profiles", "teacher_profiles_teacher_id_fkey", "teacher_id", "users", "teacher_id", {}),
        ("student_classes", "student_classes_student_id_fkey", "student_id", "student_profiles", "student_id", {}),
        ("student_id_cards", "student_id_cards_student_id_fkey", "student_id", "student_profiles", "student_id", {}),
        ("student_promotion_history", "student_promotion_history_student_id_fkey", "student_id", "student_profiles", "student_id", {}),
        ("teacher_subjects", "teacher_subjects_teacher_id_fkey", "teacher_id", "teacher_profiles", "teacher_id", {}),
    ]

    fk_created = 0
    for table, fk_name, col, ref_table, ref_col, kwargs in all_fks:
        try:
            op.create_foreign_key(fk_name, table, ref_table, [col], [ref_col], **kwargs)
            fk_created += 1
        except Exception as e:
            print(f"  WARNING: {fk_name} ({table}.{col} -> {ref_table}.{ref_col}) failed: {e}")
    print(f"Created {fk_created} FK constraints")


def downgrade() -> None:
    raise NotImplementedError("Downgrade not supported.")
