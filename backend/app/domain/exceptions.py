class DomainError(Exception):
    code = "DOMAIN_ERROR"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(DomainError):
    code = "NOT_FOUND"


class InvalidTransitionError(DomainError):
    code = "INVALID_TRANSITION"


class BusinessRuleViolationError(DomainError):
    code = "BUSINESS_RULE_VIOLATION"


class ConflictError(DomainError):
    code = "CONFLICT"
