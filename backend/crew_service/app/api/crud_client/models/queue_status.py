from enum import Enum


class QueueStatus(str, Enum):
    CLAIMED = "CLAIMED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    QUEUED = "QUEUED"

    def __str__(self) -> str:
        return str(self.value)
