from enum import Enum


class ScheduleItemPostType(str, Enum):
    POST = "Post"
    REEL = "Reel"
    STORY = "Story"

    def __str__(self) -> str:
        return str(self.value)
