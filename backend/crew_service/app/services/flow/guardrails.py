import json
import re
from datetime import datetime
from pathlib import Path
from sre_compile import MAXCODE
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


def _extract_json_from_text(text: str) -> dict | None:
    """
    Extract JSON object from text that may contain formatting or surrounding text.
    Tries multiple strategies:
    1. Parse entire text as JSON
    2. Extract JSON from markdown code blocks
    3. Find JSON object using regex
    """ 
    # Strategy 1: Try parsing the entire text as JSON
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass
    
    # Strategy 2: Extract JSON from markdown code blocks (```json ... ``` or ``` ... ```)
    code_block_pattern = r'```(?:json)?\s*\n?(.*?)```'
    matches = re.findall(code_block_pattern, text, re.DOTALL)
    for match in matches:
        try:
            return json.loads(match.strip())
        except json.JSONDecodeError:
            continue
    
    # Strategy 3: Find JSON object using regex (look for {...} pattern)
    # Find the first { and try to match balanced braces
    brace_start = text.find('{')
    if brace_start != -1:
        brace_count = 0
        brace_end = -1
        for i in range(brace_start, len(text)):
            if text[i] == '{':
                brace_count += 1
            elif text[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    brace_end = i + 1
                    break
        
        if brace_end > brace_start:
            json_candidate = text[brace_start:brace_end]
            try:
                return json.loads(json_candidate)
            except json.JSONDecodeError:
                pass
    
    return None


# def _write_failed_output_to_file(raw_output: str, expected_model_name: str) -> Path:
#     """
#     Write failed JSON parsing output to a log file for debugging.
#     Returns the path to the created file.
#     """
#     log_dir = Path("./logs/guardrail")
#     log_dir.mkdir(exist_ok=True)
    
#     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#     filename = f"failed_output_{expected_model_name}_{timestamp}.txt"
#     filepath = log_dir / filename
    
#     try:
#         with open(filepath, "w", encoding="utf-8") as f:
#             f.write(f"Failed to parse JSON for model: {expected_model_name}\n")
#             f.write(f"Timestamp: {datetime.now().isoformat()}\n")
#             f.write(f"{'='*80}\n\n")
#             f.write("Raw output:\n")
#             f.write(raw_output)
#             f.write("\n")
#         logger.info(f"Wrote failed output to {filepath}")
#     except Exception as e:
#         logger.error(f"Failed to write output to file: {e}")
    
#     return filepath


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

                if isinstance(result.raw, str):
                    # First try direct parsing
                    try:
                        parsed_json = json.loads(result.raw)
                    except json.JSONDecodeError:
                        # If that fails, try extracting JSON from formatted text
                        parsed_json = _extract_json_from_text(result.raw)
                        if parsed_json is None:
                            raise json.JSONDecodeError(
                                "Could not extract JSON from text",
                                result.raw,
                                0
                            )
                    
                    pydantic_value = expected_model.model_validate(parsed_json)
                    result.pydantic = pydantic_value
                else:
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
                logger.error(f"{reason}. Raw output preview: {str(result.raw)[:500]}")
                
                # Write full output to file for debugging
                if isinstance(result.raw, str):
                    # _write_failed_output_to_file(result.raw, expected_model.__name__)
                    logger.error("Wrote failed output to log file for debugging.")
                
                return False, reason
            except ValidationError as e:
                reason = (
                    f"Task expected structured output '{expected_model.__name__}' "
                    f"but parsed JSON failed validation: {e}"
                )
                logger.error(reason)
                return False, reason
            except Exception as e:
                reason = (
                    f"Task expected structured output '{expected_model.__name__}' "
                        f"but failed to parse/validate raw output: {e}"
                )
                logger.error(f"{reason}. Raw output preview: {str(result.raw)[:500]}")
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
                pydantic_value.model_dump(mode='json')
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
    
    MAX_CHAR_LIMIT = 15000  
    
    raw_output = str(result.raw)
    is_truncated = len(raw_output) > MAX_CHAR_LIMIT
    
    truncated_result = raw_output[:MAX_CHAR_LIMIT]
    if is_truncated:
        truncated_result += "\n...[OUTPUT TRUNCATED DUE TO LENGTH]..."

    # 2. Construct a lenient prompt that explicitly allows truncation.
    evaluation_prompt = (
        "<task_expected_output>\n"
        f"{result.expected_output}\n"
        "</task_expected_output>\n\n"
        "<task_actual_output>\n"
        f"{truncated_result}\n"
        "</task_actual_output>\n\n"
        "<your_task>\n"
        "Evaluate if the actual output meets the task requirements.\n"
        "IMPORTANT RULES FOR EVALUATION:\n"
        "1. The output provided above might be TRUNCATED due to length limits.\n"
        "2. If the output cuts off mid-stream, do NOT mark it as invalid.\n"
        "3. Focus on the STRUCTURE and CONTENT of the visible portion.\n"
        "4. If the visible content appears correct and follows the formatting rules (e.g. Markdown headers, hashtags), mark it as VALID.\n"
        "\n"
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
