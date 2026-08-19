class BackendError(Exception):
    status_code = 500
    code = "backend_error"

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class NotFoundError(BackendError):
    status_code = 404
    code = "not_found"


class ValidationError(BackendError):
    status_code = 422
    code = "validation_error"


class ModelUnavailableError(BackendError):
    status_code = 503
    code = "model_unavailable"

