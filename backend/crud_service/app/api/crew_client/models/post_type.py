from enum import Enum


class PostType(str, Enum):
    POST = "POST"
    STORY = "STORY"

    def __str__(self) -> str:
        return str(self.value)
