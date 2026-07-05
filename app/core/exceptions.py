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