from enum import Enum


class QueueStatus(str, Enum):
    CANCELLED = "CANCELLED"
    CLAIMED = "CLAIMED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    QUEUED = "QUEUED"

    def __str__(self) -> str:
        return str(self.value)
