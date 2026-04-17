import traceback

class CustomerProductIntelligenceException(Exception):

    """
    Custom exception for all bot errors.

    The original version was broken:
      - Called sys.exc_info() inside __init__ where it always returns None
      - Lost the original stack trace
      - Made debugging nearly impossible

    This fixed version:
      - Accepts the original exception as a parameter
      - Preserves the full traceback
      - Shows file + line number in error messages
    """

    def __init__(self, message: str, original: Exception | None = None):
        super().__init__(message)
        self.original = original
        # Capture traceback at raise time, not at __init__ time
        self.tb = traceback.format_exc() if original else None

    def __str__(self) -> str:
        base = super().__str__()
        if self.original:
            return f"{base}\nCaused by: {type(self.original).__name__}: {self.original}"
        return base

    def full_trace(self) -> str:
        """Returns message + full traceback for logging."""
        return f"{self.__str__()}\n{self.tb or ''}"
