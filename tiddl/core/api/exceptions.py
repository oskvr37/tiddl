TRANSIENT_STATUS_CODES = frozenset({408, 425, 429, 500, 502, 503, 504})


class ApiError(Exception):
    def __init__(self, status: int, subStatus: str, userMessage: str):
        self.status = status
        self.sub_status = subStatus
        self.user_message = userMessage

    def __str__(self):
        return f"{self.user_message}, {self.status}/{self.sub_status}"

    @property
    def is_transient(self) -> bool:
        """
        Whether the request could succeed when it is repeated later,
        as opposed to a resource that is permanently unavailable.
        """

        return self.status in TRANSIENT_STATUS_CODES


class RateLimitError(ApiError):
    """
    Raised when the API keeps responding with `429 Too Many Requests`.

    Subclass of `ApiError` so existing handlers keep working.
    """

    def __init__(
        self,
        userMessage: str = "Rate limited by Tidal API.",
        status: int = 429,
        subStatus: str = "0",
    ):
        super().__init__(status=status, subStatus=subStatus, userMessage=userMessage)
