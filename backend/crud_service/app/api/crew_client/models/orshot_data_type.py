from enum import Enum


class OrshotDataType(str, Enum):
    BACKGROUND = "BACKGROUND"
    IMAGE = "IMAGE"
    TEXT = "TEXT"

    def __str__(self) -> str:
        return str(self.value)
