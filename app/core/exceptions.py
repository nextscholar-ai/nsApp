# app/core/exceptions.py


class SchoolERPException(Exception):  # noqa: N818
    """Base exception for School ERP."""


class ValidationError(SchoolERPException):
    """Raised when validation fails."""


class NotFoundError(SchoolERPException):
    """Raised when resource not found."""


class DuplicateError(SchoolERPException):
    """Raised when duplicate entry found."""


class CapacityExceededError(SchoolERPException):
    """Raised when class capacity exceeded."""


class StudentNotEnrolledError(SchoolERPException):
    """Raised when student not enrolled in class."""


class TeacherNotAssignedError(SchoolERPException):
    """Raised when teacher not assigned to class/subject."""


class AuthenticationError(SchoolERPException):
    """Raised when authentication fails."""


class AuthorizationError(SchoolERPException):
    """Raised when user lacks permission."""


class InvalidOperationError(SchoolERPException):
    """Raised when operation is invalid."""


class SearchValidationError(ValidationError):
    """Raised when a search query fails input validation (empty, too
    long, control characters, etc). Routers translate this into a 400
    response - see app/routers/student_search_router.py.
    """


class AmbiguousIdentifierError(SchoolERPException):
    """Raised by IdentifierResolverService when a name typed by the user
    matches more than one student/teacher and the caller must pick.

    `candidates` is a list of small dicts (id, name, email, class/dept
    hint) that routers turn into a 409 response so the frontend can show
    a picker - the same "return a list, let the user choose" shape the
    existing search endpoints already use.
    """

    def __init__(self, message: str, candidates: list) -> None:
        super().__init__(message)
        self.candidates = candidates


class IdentifierNotFoundError(NotFoundError):
    """Raised by IdentifierResolverService when nothing matches the
    id / email / name typed by the user.
    """
