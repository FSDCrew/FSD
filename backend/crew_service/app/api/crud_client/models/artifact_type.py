from enum import Enum


class ArtifactType(str, Enum):
    AUDIO = "AUDIO"
    DOCUMENT = "DOCUMENT"
    IMAGE = "IMAGE"
    OTHER = "OTHER"
    TEXT = "TEXT"
    VIDEO = "VIDEO"

    def __str__(self) -> str:
        return str(self.value)
