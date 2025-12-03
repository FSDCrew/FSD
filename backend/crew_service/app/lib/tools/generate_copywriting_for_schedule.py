"""
Tool for generating Instagram copywriting for an entire social media schedule.

This tool handles iteration through all schedule items in code, ensuring
reliable processing of all items without relying on LLM to manage loops.
"""

import json
import logging
from typing import List, Type, Tuple, Union

from crewai import LLM
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from app.lib.tools.utils.validate import validate_custom_type
from app.models.models import ScheduleItem, SocialMediaSchedule, PostCaption, CopywriterOutput
from app.services.flow.llm_registry import general_llm
from app.lib.tools.markdown_to_word import markdown_to_word_doc

logger = logging.getLogger(__name__)

# Batch size for processing items (to manage context limits)
BATCH_SIZE = 15


class CopywritingOutput(BaseModel):
    """Structured output for copywriting generation."""

    caption: str = Field(..., description="The Instagram caption text")
    hashtags: List[str] = Field(..., description="List of hashtags (5-10 hashtags)")
    phrases: List[str] = Field(..., description="List of 2-3 engaging phrases or taglines")

    model_config = {"extra": "forbid"}


class BatchCopywritingOutput(BaseModel):
    """Structured output for batch copywriting generation."""

    items: List[CopywritingOutput] = Field(
        ...,
        description="List of copywriting outputs, one for each schedule item in order"
    )

    model_config = {"extra": "forbid"}


class GenerateCopywritingForScheduleInput(BaseModel):
    """Tool input - takes the entire social media schedule."""

    social_media_schedule_json: str = Field(
        ...,
        description="A SocialMediaSchedule object in JSON format containing an 'items' array of ScheduleItem objects"
    )
    crew_run_id: str = Field(
        ...,
        description="The UUID of the current crew run (required for saving the Word document artifact)"
    )


class GenerateCopywritingForScheduleTool(BaseTool):
    """
    Tool that processes an entire social media schedule and generates copywriting for all items.
    
    This tool handles iteration in code, ensuring all items are processed reliably.
    It generates copywriting in batches, accumulates results, converts to Word, and saves as artifact.
    """

    name: str = "generate_copywriting_for_schedule"
    description: str = (
        "Generates Instagram copywriting (captions, hashtags, phrases) for ALL items in a social media schedule. "
        "This tool handles iteration through all items in code, ensuring complete processing. "
        "It automatically processes items in batches, accumulates all results, "
        "converts to Word format and saves as an artifact, then returns structured CopywriterOutput data."
    )
    args_schema: Type[BaseModel] = GenerateCopywritingForScheduleInput

    def _run(self, social_media_schedule_json: str, crew_run_id: str) -> str:
        """
        Process entire schedule and generate copywriting for all items.
        
        Args:
            social_media_schedule_json: JSON string of SocialMediaSchedule object
            crew_run_id: UUID of the current crew run
            
        Returns:
            JSON string of CopywriterOutput object containing all PostCaption objects, or error message
        """
        try:
            # Handle JSON parsing - validate JSON syntax first, then normalize values
            json_string = None
            if isinstance(social_media_schedule_json, str):
                # Validate JSON syntax first
                try:
                    # Parse to check syntax
                    parsed = json.loads(social_media_schedule_json)
                except json.JSONDecodeError as json_err:
                    error_msg = (
                        f"Error: Invalid JSON format in social_media_schedule_json: {str(json_err)}. "
                        f"This usually means there are unescaped special characters (like backslashes) in the JSON. "
                        f"Please ensure the JSON is properly formatted."
                    )
                    logger.error(error_msg)
                    return error_msg
            elif isinstance(social_media_schedule_json, dict):
                parsed = social_media_schedule_json
            else:
                error_msg = f"Error: social_media_schedule_json must be a JSON string or dict, got {type(social_media_schedule_json)}"
                logger.error(error_msg)
                return error_msg
            
            # Normalize the parsed data to fix common issues
            if isinstance(parsed, dict) and "items" in parsed:
                for item in parsed.get("items", []):
                    if isinstance(item, dict):
                        # Normalize post_type: "Post" -> "POST", "Story" -> "STORY"
                        if "post_type" in item and isinstance(item["post_type"], str):
                            post_type_upper = item["post_type"].upper()
                            if post_type_upper in ["POST", "STORY"]:
                                item["post_type"] = post_type_upper
                            elif post_type_upper == "POST":
                                item["post_type"] = "POST"
                            elif post_type_upper == "STORY":
                                item["post_type"] = "STORY"
                        
                        # Normalize date: "2025-11-02T00:00:00" -> "2025-11-02"
                        if "date" in item and isinstance(item["date"], str):
                            date_str = item["date"]
                            # Extract date part if it's an ISO datetime string
                            if "T" in date_str:
                                date_str = date_str.split("T")[0]
                            item["date"] = date_str
            
            # Convert back to JSON string for validation
            json_string = json.dumps(parsed)
            
            # Parse and validate the schedule using model_validate_json (handles string-to-date/enum conversion)
            schedule_data = validate_custom_type("SocialMediaSchedule", json_string, strict=True)
            
            if not schedule_data.items or len(schedule_data.items) == 0:
                error_msg = "Error: Social media schedule contains no items."
                logger.error(error_msg)
                return error_msg

            logger.info(f"Processing {len(schedule_data.items)} schedule items for crew run {crew_run_id}")

            # Initialize accumulators for structured data and markdown
            post_captions_list: List[PostCaption] = []
            markdown_parts = ["# Instagram Campaign Copywriting\n"]

            # Process items in batches
            total_items = len(schedule_data.items)
            processed_count = 0

            for batch_start in range(0, total_items, BATCH_SIZE):
                batch_end = min(batch_start + BATCH_SIZE, total_items)
                batch_items = schedule_data.items[batch_start:batch_end]
                
                logger.info(
                    f"Processing batch: items {batch_start + 1}-{batch_end} of {total_items} "
                    f"(IDs: {[item.id for item in batch_items]})"
                )

                # Generate copywriting for this batch (returns both structured data and markdown)
                batch_result = self._generate_batch_copywriting(batch_items)
                
                # Check for error first
                if isinstance(batch_result, str):
                    if batch_result.startswith("Error:"):
                        return batch_result  # Return error immediately
                    # If it's a string but not an error, something unexpected happened
                    error_msg = f"Error: Unexpected string result from batch processing: {batch_result[:100]}"
                    logger.error(error_msg)
                    return error_msg
                
                # At this point, batch_result must be a tuple: (List[PostCaption], markdown_string)
                # Type assertion for type checker
                assert isinstance(batch_result, tuple), "batch_result should be a tuple after error check"
                batch_post_captions, batch_markdown = batch_result
                post_captions_list.extend(batch_post_captions)
                markdown_parts.append(batch_markdown)
                processed_count += len(batch_items)

            # Combine all markdown
            full_markdown = "\n".join(markdown_parts)

            # Verify we processed all items
            if processed_count != total_items:
                error_msg = (
                    f"Error: Processed {processed_count} items but expected {total_items}. "
                    f"Some items may have been skipped."
                )
                logger.error(error_msg)
                return error_msg

            if len(post_captions_list) != total_items:
                error_msg = (
                    f"Error: Generated {len(post_captions_list)} PostCaption objects but expected {total_items}. "
                    f"Some items may have been skipped."
                )
                logger.error(error_msg)
                return error_msg

            logger.info(f"Successfully generated copywriting for all {total_items} items")
            
            # Call the tool function directly (it's decorated with @tool but still callable)
            word_result = markdown_to_word_doc.func(
                markdown=full_markdown,
                file_name="post_captions.docx",
                crew_run_id=crew_run_id
            )

            if word_result and isinstance(word_result, str) and word_result.startswith("Error:"):
                logger.error(f"Failed to save Word document artifact: {word_result}")
                # Still continue - we'll return structured data even if Word conversion failed
            else:
                logger.info(f"Successfully saved Word document artifact for crew run {crew_run_id}")

            # Create CopywriterOutput object
            copywriter_output = CopywriterOutput(post_captions=post_captions_list)
            
            # Return as JSON string (this is what gets written to post_captions field)
            return copywriter_output.model_dump_json(indent=2)

        except json.JSONDecodeError as e:
            error_msg = f"Error: Invalid JSON format for social_media_schedule_json: {str(e)}"
            logger.error(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"Error generating copywriting for schedule: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg

    def _generate_batch_copywriting(self, schedule_items: List[ScheduleItem]) -> Union[Tuple[List[PostCaption], str], str]:
        """
        Generate copywriting for a batch of schedule items using LLM.
        
        Args:
            schedule_items: List of ScheduleItem objects to process
            
        Returns:
            Tuple of (List[PostCaption], markdown_string) on success, or error message string
        """
        try:
            # Create LLM with structured output for batch
            llm = LLM(
                model=general_llm.model,
                response_format=BatchCopywritingOutput,
                temperature=0.7,
            )

            # Build prompt for batch copywriting generation
            items_summary = "\n\n".join([
                f"**Item {idx + 1}:**\n"
                f"- ID: {item.id}\n"
                f"- Phase: {item.phase_name or 'N/A'}\n"
                f"- Week: {item.week or 'N/A'}\n"
                f"- Date: {item.date}\n"
                f"- Post Type: {item.post_type}\n"
                f"- Theme/Concept: {item.theme_concept}\n"
                f"- Objective: {item.objective}\n"
                f"- Description: {item.description}"
                for idx, item in enumerate(schedule_items)
            ])

            prompt = f"""You are an expert Instagram copywriter. Generate compelling copywriting for {len(schedule_items)} schedule items.

**Schedule Items (IN ORDER - process them in this exact sequence):**
{items_summary}

**CRITICAL REQUIREMENTS - READ CAREFULLY:**

1. **COMPLETE ALL ITEMS - NO SUMMARIZATION:**
   - You MUST generate copywriting for EVERY SINGLE ONE of the {len(schedule_items)} items listed above
   - Do NOT skip any items
   - Do NOT use phrases like "...and so forth for all items..." or "...(similar pattern for remaining items)..."
   - Do NOT summarize or abbreviate - generate full copywriting for each item
   - Each item requires: caption, hashtags, and phrases - generate ALL of them

2. **ORDER REQUIREMENT:**
   - You MUST return copywriting outputs in the EXACT SAME ORDER as the items listed above
   - Item 1 in your output corresponds to the first item listed, Item 2 to the second item, etc.
   - Do NOT reorder, skip, or rearrange items
   - The order is: Item IDs {[item.id for item in schedule_items]}

3. **OUTPUT FORMAT:**
   - Return a JSON object with an "items" array containing exactly {len(schedule_items)} CopywritingOutput objects
   - Each CopywritingOutput must have: caption (string), hashtags (array of strings), phrases (array of strings)
   - The array must have exactly {len(schedule_items)} elements - no more, no less

**Requirements for EACH item:**
1. Generate a compelling Instagram caption that:
   - Opens with an engaging hook
   - Tells a story or provides value based on the theme_concept and description
   - Includes a clear call-to-action (CTA) aligned with the objective
   - Is optimized for Instagram (appropriate length, emoji usage, formatting)
   - Considers the post_type (POST vs STORY may have different length requirements)

2. Generate 5-10 strategic hashtags including:
   - Broad/trending hashtags relevant to the theme_concept
   - Niche hashtags relevant to the post's theme and objective
   - Campaign-specific or branded hashtags

3. Generate 2-3 engaging phrases or taglines that:
   - Capture the essence of the post's message
   - Can be used as alternative captions or in other campaign materials
   - Are memorable and shareable

**FINAL REMINDER:**
- Generate FULL copywriting for ALL {len(schedule_items)} items - NO SUMMARIES, NO SHORTCUTS
- All hashtags should be provided WITHOUT the # symbol (the tool will format them)
- Ensure grammar, spelling, and punctuation are perfect for each item
- Make each caption engaging and optimized for Instagram
- Return a list with exactly {len(schedule_items)} items, maintaining the order: {[item.id for item in schedule_items]}
"""

            # Generate copywriting using LLM
            response = llm.call(prompt)

            # Parse response
            if isinstance(response, str):
                batch_output = BatchCopywritingOutput.model_validate_json(response)
            elif isinstance(response, dict):
                batch_output = BatchCopywritingOutput.model_validate(response)
            else:
                batch_output = response

            # Validate we got the right number of items
            if len(batch_output.items) != len(schedule_items):
                error_msg = (
                    f"Error: Expected {len(schedule_items)} copywriting outputs, "
                    f"but got {len(batch_output.items)}. "
                    f"This indicates the LLM did not generate copywriting for all items."
                )
                logger.error(error_msg)
                return error_msg

            # Validate content quality and create PostCaption objects
            post_captions_list: List[PostCaption] = []
            for idx, (item, copywriting) in enumerate(zip(schedule_items, batch_output.items)):
                if not copywriting.caption or not copywriting.caption.strip():
                    error_msg = f"Error: Item {item.id} (index {idx}) has an empty caption."
                    logger.error(error_msg)
                    return error_msg
                if not copywriting.hashtags or len(copywriting.hashtags) == 0:
                    error_msg = f"Error: Item {item.id} (index {idx}) has no hashtags."
                    logger.error(error_msg)
                    return error_msg
                if not copywriting.phrases or len(copywriting.phrases) == 0:
                    error_msg = f"Error: Item {item.id} (index {idx}) has no phrases."
                    logger.error(error_msg)
                    return error_msg

                # Check for summarization patterns
                caption_lower = copywriting.caption.lower()
                if any(pattern in caption_lower for pattern in [
                    "...and so forth",
                    "...(and so forth",
                    "...similar pattern",
                    "...remaining items",
                    "...all items",
                    "...etc for all",
                ]):
                    error_msg = (
                        f"Error: Item {item.id} (index {idx}) appears to contain summarization text. "
                        f"Each item must have unique, complete copywriting."
                    )
                    logger.error(error_msg)
                    return error_msg

                # Create PostCaption object
                post_caption = PostCaption(
                    schedule_item_id=item.id,
                    caption=copywriting.caption,
                    hashtags=copywriting.hashtags,
                    phrases=copywriting.phrases
                )
                post_captions_list.append(post_caption)

            # Format all items as markdown sections (for Word document)
            markdown_sections = []
            for item, copywriting in zip(schedule_items, batch_output.items):
                section = self._format_as_markdown(item, copywriting)
                markdown_sections.append(section)

            combined_markdown = "\n".join(markdown_sections)

            logger.info(f"Successfully generated copywriting for batch of {len(schedule_items)} items")
            return (post_captions_list, combined_markdown)

        except Exception as e:
            error_msg = f"Error generating batch copywriting: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg

    def _format_as_markdown(self, item: ScheduleItem, copywriting: CopywritingOutput) -> str:
        """Format the copywriting output as a markdown section."""
        # Format hashtags with backticks
        hashtags_formatted = "\n".join([f"- `#{tag}`" for tag in copywriting.hashtags])

        # Format phrases
        phrases_formatted = "\n".join([f"- {phrase}" for phrase in copywriting.phrases])

        # Build markdown section
        section = f"""## Item #{item.id} - Week {item.week or 'N/A'} - {item.date} - {item.post_type}

### Theme/Concept: {item.theme_concept}

### Objective: {item.objective}

### Description: {item.description}

### Caption:
{copywriting.caption}

### Hashtags:
{hashtags_formatted}

### Phrases/Taglines:
{phrases_formatted}

---
"""
        return section


# Export a ready-to-use instance of the tool
generate_copywriting_for_schedule_tool = GenerateCopywritingForScheduleTool()

