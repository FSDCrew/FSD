"""
Placeholder implementation of the generate_copywriting tool.

This version provides deterministic, static copywriting output for a given
schedule item without invoking any LLM. It is useful for testing,
documentation, or environments where the full LLM stack is unavailable.
"""

import sys
from pathlib import Path

# Fix import path when running as script - prevent local math.py from shadowing stdlib math
# This must happen BEFORE any other imports to prevent circular import issues
if __name__ == "__main__":
    # Remove script directory from path to prevent shadowing standard library modules
    script_dir = str(Path(__file__).parent.resolve())
    if script_dir in sys.path:
        sys.path.remove(script_dir)
    # Add project root to path
    project_root = Path(__file__).parent.parent.parent.parent.resolve()
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

import json
import logging
from typing import List, Type

from crewai.tools import BaseTool
from crewai import LLM
from app.services.flow.llm_registry import general_llm
from pydantic import BaseModel, Field
from app.lib.tools.utils.validate import validate_custom_type


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
            schedule_item = validate_custom_type("ScheduleItem", schedule_item_json, strict=True)

            prompt = (
                f"You are an expert Instagram copywriter. Generate compelling copywriting for the following schedule item:",
                f"**Schedule Item Details:**\n"
                f"- ID: {schedule_item.id}\n"
                f"- Phase: {schedule_item.phase_name or 'N/A'}\n"
                f"- Week: {schedule_item.week or 'N/A'}\n"
                f"- Date: {schedule_item.date}\n"
                f"- Post Type: {schedule_item.post_type}\n"
                f"- Theme/Concept: {schedule_item.theme_concept}\n"
                f"- Objective: {schedule_item.objective}\n"
                f"- Description: {schedule_item.description}\n",
                "Requirements:",
                "1. Generate a compelling Instagram caption that:\n"
                "   - Opens with an engaging hook\n"
                "   - Tells a story or provides value based on the theme_concept and description\n"
                "   - Includes a clear call-to-action (CTA) aligned with the objective\n"
                "   - Is optimized for Instagram (appropriate length, emoji usage, formatting)\n"
                "   - Considers the post_type (POST vs STORY may have different length requirements)\n",
                "2. Generate 5-10 strategic hashtags including:\n"
                "   - Broad/trending hashtags relevant to the theme_concept\n"
                "   - Niche hashtags relevant to the post's theme and objective\n"
                "   - Campaign-specific or branded hashtags\n",
                "3. Generate 2-3 engaging phrases or taglines that:\n"
                "   - Capture the essence of the post's message\n"
                "   - Can be used as alternative captions or in other campaign materials\n"
                "   - Are memorable and shareable\n",
                "CRITICAL REQUIREMENTS:\n"
                "- Generate COMPLETE copywriting for THIS SPECIFIC item - do NOT summarize or use placeholders\n"
                "- Do NOT use phrases like \"...and so forth...\" or \"...similar pattern...\" - generate unique content for this item\n"
                "- All hashtags should be provided WITHOUT the # symbol (the tool will format them)\n"
                "- Ensure grammar, spelling, and punctuation are perfect\n"
                "- Make the copy engaging and optimized for Instagram\n"
                "- This is for ONE item only - generate full copywriting (caption, hashtags, phrases) for this specific item\n"
            )
            prompt = "".join(prompt)
            
            llm = LLM(
                model=general_llm.model,
                response_format=CopywritingOutput,
                temperature=0.7,
                seed=42,
            )
            response = llm.call(prompt)
            if isinstance(response, str):
                copywriting = CopywritingOutput.model_validate_json(response)
            elif isinstance(response, dict):
                copywriting = CopywritingOutput.model_validate(response)
            else:
                copywriting = response


            # Format markdown.
            markdown = self._format_as_markdown(
                copywriting=copywriting,
            )
            logger.info("Generated placeholder copywriting for schedule item %s", schedule_item.id)
            return markdown

        except json.JSONDecodeError as exc:
            error_msg = f"Error: Invalid JSON provided – {exc}"
            logger.error(error_msg)
            return error_msg
        except Exception as exc:  # pragma: no cover

            error_msg = f"Unexpected error generating copywriting – {exc}"
            logger.error(error_msg, exc_info=True)
            return error_msg

    def _format_as_markdown(self, copywriting: CopywritingOutput) -> str:
        """Render the copywriting and schedule details as markdown."""
        hashtags_md = "\n".join([f"- `#{tag}`" for tag in copywriting.hashtags])
        phrases_md = "\n".join([f"- {phrase}" for phrase in copywriting.phrases])

        markdown = f"# Caption\n{copywriting.caption}\n\n# Hashtags\n{hashtags_md}\n\n# Phrases\n{phrases_md}"
        return markdown


# Export a ready‑to‑use instance of the tool.
generate_copywriting_tool = GenerateCopywritingTool()

# if __name__ == "__main__":
#     schedule_item = {
#         "id": 1,
#         "phase_name": "Phase 1",
#         "week": 1,
#         "date": "2023-01-01",
#         "post_type": "POST",
#         "theme_concept": "Theme Concept",
#         "objective": "Objective",
#         "description": "Description",
#     }
#     print(generate_copywriting_tool._run(schedule_item_json=json.dumps(schedule_item)))
#     with open("copywriting.md", "w") as f:
#         f.write(generate_copywriting_tool._run(schedule_item_json=json.dumps(schedule_item)))
#     print(f"Copywriting written to copywriting.md")