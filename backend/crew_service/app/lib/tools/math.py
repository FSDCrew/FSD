from __future__ import annotations

from typing import Iterable, List, Union

from crewai.tools import BaseTool, tool
from pydantic import BaseModel, Field

NumberLike = Union[int, str]


def _coerce_number(value: NumberLike) -> int:
    """
    Convert an incoming value into an integer.
    Strings may include commas (e.g., "1,234") which will be stripped.
    """
    if isinstance(value, int):
        return value

    if isinstance(value, str):
        normalized = value.replace(",", "").strip()
        if not normalized:
            raise ValueError("Cannot convert empty string to an integer.")
        return int(normalized)


def _sum_numbers(values: Iterable[NumberLike]) -> int:
    return sum(_coerce_number(value) for value in values)


class VerifySumEqualsExpectedInput(BaseModel):
    """Input schema for verify sum equals expected tool."""
    expected_total: Union[int, str] = Field(
        ..., 
        description="The reference total (int/str). Strings like '10' are supported."
    )
    values: List[Union[int, str]] = Field(
        ..., 
        description="Sequence of numbers to sum. Each entry can be an int or numeric string."
    )


class VerifySumEqualsExpectedTool(BaseTool):
    name: str = "verify sum equals expected"
    description: str = (
        "Validate that the sum of `values` equals the `expected_total`.\n\n"
        "Args:\n"
        "    expected_total: The reference total (int/str). Strings like \"10\" are supported.\n"
        "    values: Sequence of numbers to sum. Each entry can be an int or numeric string.\n\n"
        "Returns:\n"
        "    str: A human-readable message indicating whether the sums match."
    )
    args_schema: type[BaseModel] = VerifySumEqualsExpectedInput

    def _run(
        self, 
        expected_total: Union[int, str], 
        values: List[Union[int, str]]
    ) -> str:
        if not isinstance(values, list) or len(values) == 0:
            raise ValueError("`values` must be a non-empty list of numbers.")

        numeric_total = _coerce_number(expected_total)
        actual_total = _sum_numbers(values)
        difference = actual_total - numeric_total

        if difference == 0:
            return (
                f"Success: The values sum to {actual_total}, matching the expected total "
                f"of {numeric_total}."
            )

        return (
            "Mismatch: "
            f"expected total {numeric_total}, but the values sum to {actual_total} "
            f"(difference {difference})."
        )


# Create the tool instance for backward compatibility
verify_sum_equals_expected = VerifySumEqualsExpectedTool()
