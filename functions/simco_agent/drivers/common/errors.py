from enum import Enum

class DriverErrorCode(str, Enum):
    AUTH_FAILED = "AUTH_FAILED"
    CONNECTION_REFUSED = "CONNECTION_REFUSED"
    TIMEOUT = "TIMEOUT"
    PROTOCOL_ERROR = "PROTOCOL_ERROR"
    DEPENDENCY_MISSING = "DEPENDENCY_MISSING"
    UNKNOWN = "UNKNOWN"

class DriverError(Exception):
    """Base class for all driver-related errors."""
    def __init__(self, message: str, code: DriverErrorCode = DriverErrorCode.UNKNOWN, details: dict = None):
        super().__init__(message)
        self.code = code
        self.details = details or {}

class HandshakeError(DriverError):
    """Raised during fingerprinting/handshake failure."""
    pass

class TelemetryError(DriverError):
    """Raised during read cycle failure."""
    pass
