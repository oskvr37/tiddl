class ApiError(Exception):
    def __init__(self, status: int, subStatus: str, userMessage: str):
        self.status = status
        self.sub_status = subStatus
        self.user_message = userMessage

    def __str__(self):
        return f"{self.user_message}, {self.status}/{self.sub_status}"
