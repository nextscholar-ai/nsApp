from .common import (
    BaseSchema,
    TimestampSchema,
    ActiveSchema,
    AuditSchema,
    UserMinResponse,
    StudentProfileMinResponse,
    TeacherProfileMinResponse,
    ClassRoomMinResponse,
    SubjectMinResponse,
    AcademicSessionMinResponse,
    ResponseSchema,
    PaginatedResponseSchema,
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    LogoutRequest,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    VerifyEmailRequest,
    ResendOTPRequest,
)

from .academic_session import (
    AcademicSessionBase,
    AcademicSessionCreate,
    AcademicSessionResponse,
    AcademicSessionUpdate,
)

from .user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    StudentProfileBase,
    StudentProfileCreate,
    StudentProfileUpdate,
    StudentProfileResponse,
    TeacherProfileBase,
    TeacherProfileCreate,
    TeacherProfileUpdate,
    TeacherProfileResponse,
    AdminProfileBase,
    AdminProfileCreate,
    AdminProfileUpdate,
    AdminProfileResponse,
)

from .classes_subjects import (
    ClassRoomBase,
    ClassRoomCreate,
    ClassRoomUpdate,
    ClassRoomResponse,
    SubjectBase,
    SubjectCreate,
    SubjectUpdate,
    SubjectResponse,
    ClassSubjectBase,
    ClassSubjectCreate,
    ClassSubjectResponse,
)

from .teacher_student_links import (
    TeacherSubjectBase,
    TeacherSubjectCreate,
    TeacherSubjectResponse,
    StudentClassBase,
    StudentClassCreate,
    StudentClassResponse,
    StudentPromotionHistoryBase,
    StudentPromotionHistoryCreate,
    StudentPromotionHistoryResponse,
)

from .timetable import (
    WeekDayBase,
    WeekDayResponse,
    TimeSlotBase,
    TimeSlotResponse,
    ClassTimeTableBase,
    ClassTimeTableCreate,
    ClassTimeTableResponse,
    TeacherAvailabilityBase,
    TeacherAvailabilityCreate,
    TeacherAvailabilityResponse,
    WeekDayCreate,
    TimeSlotCreate,
    ClassTimeTableUpdate,
    TeacherAvailabilityUpdate,
)

from .timetable_student_teacher import (
    StudentTimetableItemResponse,
    TeacherTimetableItemResponse,
)

from .daily_class import (
    DailyClassBase,
    DailyClassCreate,
    DailyClassResponse,
    DailyClassStudentBase,
    DailyClassStudentCreate,
    DailyClassStudentResponse,
    StudentAttendanceBase,
    StudentAttendanceResponse,
    DailyClassUpdate,
    DailyClassStudentUpdate,
)

from .admin_student_teacher import (
    TeacherAdminListResponse,
    StudentAdminListResponse,
    PaginatedTeacherAdminListResponse,
    PaginatedStudentAdminListResponse,
)

from .assignment import (
    AssignmentBase,
    AssignmentCreate,
    AssignmentResponse,
    AssignmentResultBase,
    AssignmentResultCreate,
    AssignmentResultResponse,
    AssignmentUpdate,
    AssignmentResultUpdate,
)

from .study_material import (
    StudyMaterialBase,
    StudyMaterialCreate,
    StudyMaterialResponse,
    StudyMaterialUpdate,
)

from .exam import (
    ExamBase,
    ExamCreate,
    ExamResponse,
    ExamResultBase,
    ExamResultCreate,
    ExamResultResponse,
    ExamUpdate,
    ExamResultUpdate,
)

from .fee import (
    FeeBase,
    FeeCreate,
    FeeResponse,
    FeeUpdate,
    FeePaymentCreate,
    FeePaymentResponse,
    FeeSummaryResponse,
)

from .notice import (
    NoticeBase,
    NoticeCreate,
    NoticeResponse,
    NoticeUpdate,
    NoticeFilterRequest,
)

from .chat import (
    ChatRoomBase,
    ChatRoomCreate,
    ChatRoomResponse,
    ChatMessageBase,
    ChatMessageCreate,
    ChatMessageResponse,
    ChatRoomUpdate,
    ChatConversationResponse,
    ChatUnreadCountResponse,
)

from .student_id_card import (
    StudentIDCardGenerateResponse,
    StudentIDCardResponse,
    StudentIDCardDownloadResponse,
    PaginatedStudentIDCardListResponse,
)

from .search import (
    StudentSearchResultItem,
    StudentSearchResponse,
)

# ============================================================
# Rebuild models with forward references (e.g. LoginResponse.user: 'UserResponse')
# now that all schema classes are imported into this namespace.
# ============================================================
LoginResponse.model_rebuild()

