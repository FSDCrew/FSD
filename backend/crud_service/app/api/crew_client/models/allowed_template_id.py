from enum import IntEnum


class AllowedTemplateId(IntEnum):
    VALUE_1201 = 1201
    VALUE_1909 = 1909

    def __str__(self) -> str:
        return str(self.value)
