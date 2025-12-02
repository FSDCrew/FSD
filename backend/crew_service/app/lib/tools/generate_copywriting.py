"""
Placeholder implementation of the generate_copywriting tool.

This version provides deterministic, static copywriting output for a given
schedule item without invoking any LLM. It is useful for testing,
documentation, or environments where the full LLM stack is unavailable.
"""

import json
import logging
from typing import List, Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

# Import the ScheduleItem model for type consistency.
# If the import fails (e.g., in a pure test environment), the code will still
# operate on the raw dictionary.
try:
    from app.models.models import ScheduleItem  # type: ignore
except Exception:  # pragma: no cover
    ScheduleItem = dict  # Fallback placeholder


logger = logging.getLogger(__name__)


class CopywritingOutput(BaseModel):
    """Structured copywriting output."""

    caption: str = Field(..., description="Instagram caption")
    hashtags: List[str] = Field(..., description="List of hashtags (without '#')")
    phrases: List[str] = Field(..., description="List of short taglines/phrases")

    model_config = {"extra": "forbid"}


class GenerateCopywritingInput(BaseModel):
    """Tool input – a JSON string representing a single ScheduleItem."""

    schedule_item_json: str = Field(
        ...,
        description=(
            "JSON representation of a ScheduleItem containing at minimum "
            "'id', 'phase_name', 'week', 'date', 'post_type', "
            "'theme_concept', 'objective', and 'description'."
        ),
    )


class GenerateCopywritingTool(BaseTool):
    """Simple placeholder tool that returns static copywriting."""

    name: str = "generate_copywriting_for_item"
    description: str = (
        "Generates placeholder Instagram copywriting (caption, hashtags, phrases) "
        "for a single schedule item. The output is deterministic and does not "
        "invoke any external LLM services."
    )
    args_schema: Type[BaseModel] = GenerateCopywritingInput

    def _run(self, schedule_item_json: str) -> str:
        """
        Parse the input JSON and return a markdown representation with static
        copywriting values.
        """
        try:
            # Load the JSON into a dict; we deliberately avoid heavy validation.
            item_data = json.loads(schedule_item_json)

            # Ensure required keys exist – fallback to placeholders if missing.
            item_id = item_data.get("id", "unknown")
            phase = item_data.get("phase_name", "N/A")
            week = item_data.get("week", "N/A")
            date = item_data.get("date", "N/A")
            post_type = item_data.get("post_type", "N/A")
            theme = item_data.get("theme_concept", "N/A")
            objective = item_data.get("objective", "N/A")
            description = item_data.get("description", "N/A")

            # Build a static CopywritingOutput.
            copywriting = CopywritingOutput(
                caption=f"Placeholder caption for item {item_id}.",
                hashtags=["placeholder1", "placeholder2", "placeholder3"],
                phrases=["Placeholder phrase 1.", "Placeholder phrase 2."],
            )

            # Format markdown.
            markdown = self._format_as_markdown(
                schedule_item=dict(
                    id=item_id,
                    phase_name=phase,
                    week=week,
                    date=date,
                    post_type=post_type,
                    theme_concept=theme,
                    objective=objective,
                    description=description,
                ),
                copywriting=copywriting,
            )
            logger.info("Generated placeholder copywriting for schedule item %s", item_id)
            return markdown

        except json.JSONDecodeError as exc:
            error_msg = f"Error: Invalid JSON provided – {exc}"
            logger.error(error_msg)
            return error_msg
        except Exception as exc:  # pragma: no cover

            error_msg = f"Unexpected error generating copywriting – {exc}"
            logger.error(error_msg, exc_info=True)
            return error_msg

    def _format_as_markdown(self, schedule_item: dict, copywriting: CopywritingOutput) -> str:
        """Render the copywriting and schedule details as markdown."""
        hashtags_md = "\n".join([f"- `#{tag}`" for tag in copywriting.hashtags])
        phrases_md = "\n".join([f"- {phrase}" for phrase in copywriting.phrases])

        markdown = f"""## Item #{schedule_item.get('id')} – Week {schedule_item.get('week')} – {schedule_item.get('date')} – {schedule_item.get('post_type')}

### Theme/Concept
{schedule_item.get('theme_concept')}

### Objective
{schedule_item.get('objective')}

### Description
{schedule_item.get('description')}

### Caption
{copywriting.caption}

### Hashtags
{hashtags_md}

### Phrases
{phrases_md}
"""
        return markdown


# Export a ready‑to‑use instance of the tool.
generate_copywriting_tool = GenerateCopywritingTool()