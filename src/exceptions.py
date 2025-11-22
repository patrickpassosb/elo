class EloError(Exception):
    """Base exception for ELO application."""
    pass

class ConfigurationError(EloError):
    """Raised when there is a configuration issue."""
    pass

class APIError(EloError):
    """Raised when an external API call fails."""
    pass

class MediaError(EloError):
    """Raised when there is an error handling media files."""
    pass

class ValidationError(EloError):
    """Raised when input validation fails."""
    pass
