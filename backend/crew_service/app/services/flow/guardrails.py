from typing import Any, Callable, Sequence, Tuple, Type

from crewai import LLM, TaskOutput
from crewai.tasks.output_format import OutputFormat
from pydantic import BaseModel, ValidationError

from config import logger

GuardrailCallable = Callable[[TaskOutput], Tuple[bool, Any]]


class GuardrailResponseFormat(BaseModel):
    """Structured response format used by the judge LLM."""

    valid: bool
    reason: str


judge_llm = LLM(
    model="openai/gpt-4.1-mini",
    temperature=0.7,
    seed=42,
    response_format=GuardrailResponseFormat,
)


def structured_output_guardrail(
    expected_model: Type[BaseModel],
) -> GuardrailCallable:
    """
    Factory that builds a guardrail bound to a specific Pydantic model.

    Usage:
        guardrails_to_use.append(structured_output_guardrail(MyModel))
    """

    def structured_output_guardrail(result: TaskOutput) -> Tuple[bool, Any]:
        """Ensure the structured output aligns with the expected Pydantic model."""
        if result.output_format != OutputFormat.PYDANTIC:
            reason = (
                f"Task expected structured output '{expected_model.__name__}' "
                f"but produced '{result.output_format.value}'."
            )
            logger.error(reason)
            return False, reason

        pydantic_value = result.pydantic

        if pydantic_value is None and result.output_format == OutputFormat.PYDANTIC:
            try:
                import json

                # Try to parse raw as JSON string
                if isinstance(result.raw, str):
                    parsed_json = json.loads(result.raw)
                    # Validate against expected model
                    pydantic_value = expected_model.model_validate(parsed_json)
                    # Set it on the result object so it's available downstream
                    result.pydantic = pydantic_value
                else:
                    # If raw is already a dict, try to validate directly
                    if isinstance(result.raw, dict):
                        pydantic_value = expected_model.model_validate(result.raw)
                        result.pydantic = pydantic_value
                    else:
                        reason = (
                            f"Task expected structured output '{expected_model.__name__}' "
                            f"but raw output is neither JSON string nor dict "
                            f"(type: {type(result.raw)})."
                        )
                        return False, reason
            except json.JSONDecodeError as e:
                reason = (
                    f"Task expected structured output '{expected_model.__name__}' "
                    f"but failed to parse raw output as JSON: {e}"
                )
                return False, reason
            except ValidationError as e:
                reason = (
                    f"Task expected structured output '{expected_model.__name__}' "
                    f"but parsed JSON failed validation: {e}"
                )
                return False, reason
            except Exception as e:
                reason = (
                    f"Task expected structured output '{expected_model.__name__}' "
                        f"but failed to parse/validate raw output: {e}"
                )
                return False, reason

        if pydantic_value is None:
            reason = (
                f"Task expected structured output '{expected_model.__name__}' "
                "but no Pydantic payload was returned."
            )
            logger.error(reason)
            return False, reason

        if not isinstance(pydantic_value, BaseModel):
            reason = (
                f"Structured output for '{expected_model.__name__}' "
                "was not a Pydantic model."
            )
            logger.error(reason)
            logger.error(f"Pydantic value type: {type(pydantic_value)}")
            logger.error(f"Pydantic value: {pydantic_value}")
            return False, reason

        try:
            validated_payload = expected_model.model_validate(
                pydantic_value.model_dump()
            )
            result.pydantic = validated_payload
        except ValidationError as exc:
            reason = f"Structured output failed {expected_model.__name__} validation: {exc}"
            logger.error(reason)
            return False, reason

        return True, result

    structured_output_guardrail.__name__ = "structured_output_guardrail"
    structured_output_guardrail.__qualname__ = "structured_output_guardrail"
    structured_output_guardrail.__doc__ = (
        structured_output_guardrail.__doc__
    )

    return structured_output_guardrail


def llm_judge_guardrail(result: TaskOutput) -> Tuple[bool, Any]:
    """Validate task output content using an LLM judge."""

    evaluation_prompt = (
        "<task_expected_output>\n"
        f"{result.expected_output}\n"
        "</task_expected_output>\n\n"
        "<task_actual_output>\n"
        f"{result.raw}\n"
        "</task_actual_output>\n\n"
        "<your_task>\n"
        "Evaluate if the actual output meets the task requirements.\n"
        "Respond ONLY with JSON format.\n"
        "{\n"
        '    "valid": boolean,\n'
        '    "reason": string\n'
        "}\n"
        "</your_task>\n"
    )

    response = judge_llm.call([{"role": "user", "content": evaluation_prompt}])

    if isinstance(response, str):
        parsed = GuardrailResponseFormat.model_validate_json(response)
    elif isinstance(response, dict):
        parsed = GuardrailResponseFormat.model_validate(response)
    else:
        parsed = response

    if not parsed.valid:
        logger.error(f"Guardrail validation failed: {parsed.reason}")
        return False, parsed.reason

    return True, result


def compose_guardrails(guardrails: Sequence[GuardrailCallable]) -> GuardrailCallable:
    """Chain multiple guardrails so each validates before the next runs."""

    def runner(result: TaskOutput) -> Tuple[bool, Any]:
        if not guardrails:
            return True, result.raw

        current_output = result
        last_result: Any = result
        for guard in guardrails:
            success, guard_result = guard(current_output)
            if not success:
                return False, guard_result

            last_result = guard_result
            if isinstance(guard_result, TaskOutput):
                current_output = guard_result

        return True, last_result

    return runner
