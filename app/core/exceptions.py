# app/core/exceptions.py

class SchoolERPException(Exception):
    """Base exception for School ERP"""
    pass

class ValidationError(SchoolERPException):
    """Raised when validation fails"""
    pass

class NotFoundError(SchoolERPException):
    """Raised when resource not found"""
    pass

class DuplicateError(SchoolERPException):
    """Raised when duplicate entry found"""
    pass

class CapacityExceededError(SchoolERPException):
    """Raised when class capacity exceeded"""
    pass

class StudentNotEnrolledError(SchoolERPException):
    """Raised when student not enrolled in class"""
    pass

class TeacherNotAssignedError(SchoolERPException):
    """Raised when teacher not assigned to class/subject"""
    pass

class AuthenticationError(SchoolERPException):
    """Raised when authentication fails"""
    pass

class AuthorizationError(SchoolERPException):
    """Raised when user lacks permission"""
    pass

class InvalidOperationError(SchoolERPException):
    """Raised when operation is invalid"""
    pass

class SearchValidationError(ValidationError):
    """Raised when a search query fails input validation (empty, too
    long, control characters, etc). Routers translate this into a 400
    response - see app/routers/student_search_router.py."""
    pass


class AmbiguousIdentifierError(SchoolERPException):
    """Raised by IdentifierResolverService when a name typed by the user
    matches more than one student/teacher and the caller must pick.

    `candidates` is a list of small dicts (id, name, email, class/dept
    hint) that routers turn into a 409 response so the frontend can show
    a picker - the same "return a list, let the user choose" shape the
    existing search endpoints already use.
    """

    def __init__(self, message: str, candidates: list):
        super().__init__(message)
        self.candidates = candidates


class IdentifierNotFoundError(NotFoundError):
    """Raised by IdentifierResolverService when nothing matches the
    id / email / name typed by the user."""
    pass
