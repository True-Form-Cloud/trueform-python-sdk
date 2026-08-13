class TrueformError(Exception):
    def __init__(
        self,
        message: str,
        *,
        code: str,
        status: int | None = None,
        request_id: str | None = None,
        retry_after: float | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.status = status
        self.request_id = request_id
        self.retry_after = retry_after


class APIError(TrueformError):
    pass


class InvalidRequestError(APIError):
    pass


class RateLimitError(APIError):
    pass


class ConnectionError(TrueformError):
    pass


class TimeoutError(ConnectionError):
    pass