from enum import Enum


class TaskStatus(str, Enum):
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"

    def __str__(self) -> str:
        return str(self.value)
