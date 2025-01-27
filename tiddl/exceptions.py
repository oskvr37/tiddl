class AuthError(Exception):
    def __init__(
        self, status: int, error: str, sub_status: str, error_description: str
    ):
        self.status = status
        self.error = error
        self.sub_status = sub_status
        self.error_description = error_description

    def __str__(self):
        return f"{self.status}: {self.error} - {self.error_description}"


class ApiError(Exception):
    def __init__(self, status: int, subStatus: str, userMessage: str):
        self.status = status
        self.sub_status = subStatus
        self.user_message = userMessage

    def __str__(self):
        return f"{self.user_message} ({self.status} - {self.sub_status})"
