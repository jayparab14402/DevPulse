import enum

# Python Enum
# enum.Enum -> Fixed values define karta hai
# str -> Values ko string-compatible banata hai
class ErrorLevel(str, enum.Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
