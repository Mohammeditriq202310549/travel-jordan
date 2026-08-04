import os
import traceback
from datetime import datetime

# Path for error log file
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
LOG_FILE_PATH = os.path.join(LOG_DIR, "errors.log")


def ensure_log_dir_exists():
    """Creates logs directory if it does not exist."""
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)


def log_exception(error, context="General"):
    """
    Logs exceptions into app/logs/errors.log with formatted timestamps and stack trace.
    Returns the formatted log string.
    """
    ensure_log_dir_exists()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    error_type = type(error).__name__
    error_msg = str(error)
    stack_trace = traceback.format_exc()

    log_entry = (
        f"==================================================\n"
        f"TIMESTAMP  : [{timestamp}]\n"
        f"CONTEXT    : [{context}]\n"
        f"ERROR TYPE : {error_type}\n"
        f"MESSAGE    : {error_msg}\n"
        f"TRACEBACK  :\n{stack_trace}"
        f"==================================================\n\n"
    )

    try:
        with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        print("Failed to write to error log file:", e)

    return log_entry


# Custom Application Exception Classes
class AppBaseException(Exception):
    """Base class for custom application exceptions."""
    def __init__(self, message="An application error occurred.", status_code=500):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class DatabaseException(AppBaseException):
    """Raised when database query or connection fails."""
    def __init__(self, message="Database operation failed.", status_code=500):
        super().__init__(message, status_code)


class AuthenticationException(AppBaseException):
    """Raised when user authentication or permission fails."""
    def __init__(self, message="Authentication failed.", status_code=401):
        super().__init__(message, status_code)


class ValidationException(AppBaseException):
    """Raised when user input validation fails."""
    def __init__(self, message="Invalid input data.", status_code=400):
        super().__init__(message, status_code)


class ResourceNotFoundException(AppBaseException):
    """Raised when a requested resource is not found."""
    def __init__(self, message="Resource not found.", status_code=404):
        super().__init__(message, status_code)
