import enum

# Python Enum
# enum.Enum -> Fixed values define karta hai
# str -> Values ko string-compatible banata hai
class ErrorLevel(str, enum.Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class MonitorStatus(str, enum.Enum):
    UP = "UP"
    DOWN = "DOWN"

class IncidentStatus(str, enum.Enum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"


class IncidentSeverity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
