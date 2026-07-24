# ruff: noqa: F401

from app.core.enums import UserRole

from .academic_session import (
    AcademicSessionBase,
    AcademicSessionCreate,
    AcademicSessionResponse,
    AcademicSessionUpdate,
)
from .admin_student_teacher import (
    PaginatedStudentAdminListResponse,
    PaginatedTeacherAdminListResponse,
    StudentAdminListResponse,
    TeacherAdminListResponse,
)
from .assignment import (
    AssignmentBase,
    AssignmentCreate,
    AssignmentResponse,
    AssignmentResultBase,
    AssignmentResultCreate,
    AssignmentResultResponse,
    AssignmentResultUpdate,
    AssignmentUpdate,
)
from .chat import (
    ChatConversationResponse,
    ChatMessageBase,
    ChatMessageCreate,
    ChatMessageResponse,
    ChatRoomBase,
    ChatRoomCreate,
    ChatRoomResponse,
    ChatRoomUpdate,
    ChatUnreadCountResponse,
)
from .classes_subjects import (
    ClassRoomBase,
    ClassRoomCreate,
    ClassRoomResponse,
    ClassRoomUpdate,
    ClassSubjectBase,
    ClassSubjectCreate,
    ClassSubjectResponse,
    SubjectBase,
    SubjectCreate,
    SubjectResponse,
    SubjectUpdate,
)
from .common import (
    AcademicSessionMinResponse,
    ActiveSchema,
    AuditSchema,
    BaseSchema,
    ChangePasswordRequest,
    ClassRoomMinResponse,
    ForgotPasswordRequest,
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    PaginatedResponseSchema,
    RefreshTokenRequest,
    RefreshTokenResponse,
    ResendOTPRequest,
    ResetPasswordRequest,
    ResponseSchema,
    StudentProfileMinResponse,
    SubjectMinResponse,
    TeacherProfileMinResponse,
    TimestampSchema,
    UserMinResponse,
    VerifyEmailRequest,
)
from .daily_class import (
    DailyClassBase,
    DailyClassCreate,
    DailyClassResponse,
    DailyClassStudentBase,
    DailyClassStudentCreate,
    DailyClassStudentResponse,
    DailyClassStudentUpdate,
    DailyClassUpdate,
    StudentAttendanceBase,
    StudentAttendanceResponse,
)
from .exam import (
    ExamBase,
    ExamCreate,
    ExamResponse,
    ExamResultBase,
    ExamResultCreate,
    ExamResultResponse,
    ExamResultUpdate,
    ExamUpdate,
)
from .fee import (
    FeeBase,
    FeeCreate,
    FeePaymentCreate,
    FeePaymentResponse,
    FeeResponse,
    FeeSummaryResponse,
    FeeUpdate,
)
from .ka import (
    KaCourseCreate,
    KaCourseResponse,
    KaStudentCreate,
    KaStudentResponse,
    StudentReportCreate,
    StudentReportResponse,
)
from .notice import (
    NoticeBase,
    NoticeCreate,
    NoticeFilterRequest,
    NoticeResponse,
    NoticeUpdate,
)
from .promotion import (
    StudentPromotionHistoryCreate,
    StudentPromotionHistoryResponse,
    StudentPromotionHistoryUpdate,
)
from .search import (
    StudentSearchDetail,
    StudentSearchResponse,
    TeacherSearchDetail,
    TeacherSearchResponse,
)
from .student_id_card import (
    PaginatedStudentIDCardListResponse,
    StudentIDCardDownloadResponse,
    StudentIDCardGenerateResponse,
    StudentIDCardResponse,
)
from .study_material import (
    StudyMaterialBase,
    StudyMaterialCreate,
    StudyMaterialResponse,
    StudyMaterialUpdate,
)
from .teacher_student_links import (
    StudentClassBase,
    StudentClassCreate,
    StudentClassResponse,
    StudentPromotionHistoryBase,
    TeacherSubjectBase,
    TeacherSubjectCreate,
    TeacherSubjectResponse,
)
from .timetable import (
    ClassTimeTableBase,
    ClassTimeTableCreate,
    ClassTimeTableResponse,
    ClassTimeTableUpdate,
    TeacherAvailabilityBase,
    TeacherAvailabilityCreate,
    TeacherAvailabilityResponse,
    TeacherAvailabilityUpdate,
    TimeSlotBase,
    TimeSlotCreate,
    TimeSlotResponse,
    WeekDayBase,
    WeekDayCreate,
    WeekDayResponse,
)
from .timetable_student_teacher import (
    StudentTimetableItemResponse,
    TeacherTimetableItemResponse,
)
from .topic import (
    StudentTopicProgressReportCreate,
    StudentTopicProgressReportResponse,
    TopicCreate,
    TopicProgressCreate,
    TopicProgressResponse,
    TopicResponse,
)
from .user import (
    AdminProfileBase,
    AdminProfileCreate,
    AdminProfileResponse,
    AdminProfileUpdate,
    StudentProfileBase,
    StudentProfileCreate,
    StudentProfileResponse,
    StudentProfileUpdate,
    TeacherProfileBase,
    TeacherProfileCreate,
    TeacherProfileResponse,
    TeacherProfileUpdate,
    UserBase,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from .zoom import (
    ZoomDurationReportCreate,
    ZoomDurationReportResponse,
    ZoomDurationReportUpdate,
    ZoomFileCreate,
    ZoomFileResponse,
    ZoomFileUpdate,
    ZoomInteractionReportCreate,
    ZoomInteractionReportResponse,
    ZoomInteractionReportUpdate,
    ZoomMeetingCreate,
    ZoomMeetingResponse,
    ZoomMeetingUpdate,
    ZoomRecordingFileCreate,
    ZoomRecordingFileResponse,
    ZoomRecordingFileUpdate,
    ZoomStudentInteractionCreate,
    ZoomStudentInteractionResponse,
    ZoomStudentInteractionUpdate,
    ZoomTranscriptCreate,
    ZoomTranscriptResponse,
    ZoomTranscriptUpdate,
)

# ============================================================
# Rebuild models with forward references (e.g. LoginResponse.user: 'UserResponse')
# now that all schema classes are imported into this namespace.
# ============================================================
LoginResponse.model_rebuild()
UserResponse.model_rebuild()
StudentProfileResponse.model_rebuild()
TeacherProfileResponse.model_rebuild()
AdminProfileResponse.model_rebuild()
AssignmentResponse.model_rebuild()
