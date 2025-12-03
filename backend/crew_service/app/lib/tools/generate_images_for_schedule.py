"""
Tool for generating images for an entire social media schedule.

This tool handles iteration through all schedule items in code, ensuring
reliable processing of all items without relying on LLM to manage loops.
"""

import json
import logging
from typing import List, Type

from crewai import LLM
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from app.lib.tools.imagen_generator import generate_imagen_tool
from app.lib.tools.utils.validate import validate_custom_type
from app.models.models import ScheduleItem, SocialMediaSchedule, ImageAsset
from app.services.flow.llm_registry import general_llm

logger = logging.getLogger(__name__)


class ImagePromptOutput(BaseModel):
    """Structured output for image prompt generation."""

    prompt: str = Field(..., description="A detailed, high-quality image generation prompt")

    model_config = {"extra": "forbid"}


class GenerateImagesForScheduleInput(BaseModel):
    """Tool input - takes the entire social media schedule."""

    social_media_schedule_json: str = Field(
        ...,
        description="A SocialMediaSchedule object in JSON format containing an 'items' array of ScheduleItem objects"
    )
    crew_run_id: str = Field(
        ...,
        description="The UUID of the current crew run (required for saving image artifacts)"
    )


class GenerateImagesForScheduleTool(BaseTool):
    """
    Tool that processes an entire social media schedule and generates images for all items.
    
    This tool handles iteration in code, ensuring all items are processed reliably.
    It generates image prompts based on schedule item context, then generates images using Imagen.
    """

    name: str = "generate_images_for_schedule"
    description: str = (
        "Generates images for ALL items in a social media schedule. "
        "This tool handles iteration through all items in code, ensuring complete processing. "
        "For each schedule item, it generates a detailed image prompt (with no text) based on the item's theme_concept, "
        "description, objective, and post_type, then generates the image using Imagen. "
        "Returns a JSON array of ImageAsset objects with S3 URLs for all generated images."
    )
    args_schema: Type[BaseModel] = GenerateImagesForScheduleInput

    def _run(
        self,
        social_media_schedule_json: str,
        crew_run_id: str,
    ) -> str:
        """
        Process entire schedule and generate images for all items.
        
        Args:
            social_media_schedule_json: JSON string of SocialMediaSchedule object
            crew_run_id: UUID of the current crew run
            
        Returns:
            JSON string array of ImageAsset objects (one per schedule item), or error message
        """
        try:
            # Handle JSON parsing - validate JSON syntax first, then normalize values
            if isinstance(social_media_schedule_json, str):
                try:
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

                        # Normalize date: "2025-11-02T00:00:00" -> "2025-11-02"
                        if "date" in item and isinstance(item["date"], str):
                            date_str = item["date"]
                            if "T" in date_str:
                                date_str = date_str.split("T")[0]
                            item["date"] = date_str

            # Convert back to JSON string for validation
            json_string = json.dumps(parsed)

            # Parse and validate the schedule
            schedule_data = validate_custom_type("SocialMediaSchedule", json_string, strict=True)

            if not schedule_data.items or len(schedule_data.items) == 0:
                error_msg = "Error: Social media schedule contains no items."
                logger.error(error_msg)
                return error_msg

            logger.info(f"Processing {len(schedule_data.items)} schedule items for image generation (crew run {crew_run_id})")

            # Process each item and generate images
            image_assets_list: List[ImageAsset] = []
            failed_items = []

            for item in schedule_data.items:
                try:
                    logger.info(f"Processing schedule item {item.id} (item {len(image_assets_list) + 1} of {len(schedule_data.items)})")

                    # Generate image prompt based on item context
                    image_prompt = self._generate_image_prompt(item=item)

                    if image_prompt.startswith("Error:"):
                        error_msg = f"Failed to generate prompt for item {item.id}: {image_prompt}"
                        logger.error(error_msg)
                        failed_items.append({"item_id": item.id, "error": error_msg})
                        # Continue with next item instead of failing completely
                        continue

                    # Generate image using Imagen
                    logger.info(f"Calling generate_imagen_tool for item {item.id}")
                    image_url = generate_imagen_tool._run(
                        prompt=image_prompt,
                        crew_run_id=crew_run_id
                    )

                    if image_url.startswith("Error:"):
                        error_msg = f"Failed to generate image for item {item.id}: {image_url}"
                        logger.error(error_msg)
                        failed_items.append({"item_id": item.id, "error": error_msg})
                        # Continue with next item instead of failing completely
                        continue

                    # Create ImageAsset object
                    image_asset = ImageAsset(
                        schedule_item_id=item.id,
                        image_url=image_url
                    )
                    image_assets_list.append(image_asset)
                    logger.info(f"Successfully generated image for item {item.id}: {image_url[:50]}...")

                except Exception as item_error:
                    error_msg = f"Unexpected error processing item {item.id}: {str(item_error)}"
                    logger.error(error_msg, exc_info=True)
                    failed_items.append({"item_id": item.id, "error": error_msg})
                    # Continue with next item
                    continue

            # Validate that we processed all items
            if len(image_assets_list) != len(schedule_data.items):
                missing_count = len(schedule_data.items) - len(image_assets_list)
                warning_msg = (
                    f"WARNING: Only generated {len(image_assets_list)} images out of {len(schedule_data.items)} items. "
                    f"Missing {missing_count} item(s). Failed items: {failed_items}"
                )
                logger.warning(warning_msg)
                
                # If no images were generated at all, return error
                if len(image_assets_list) == 0:
                    error_msg = f"Error: Failed to generate any images. All {len(schedule_data.items)} image generation attempts failed. Errors: {failed_items}"
                    logger.error(error_msg)
                    return error_msg

            logger.info(f"Successfully generated {len(image_assets_list)} images out of {len(schedule_data.items)} items")
            
            # Log any failures for debugging
            if failed_items:
                logger.warning(f"Failed to generate images for {len(failed_items)} item(s): {failed_items}")

            # Return as JSON array string (list of ImageAsset objects)
            return json.dumps([asset.model_dump() for asset in image_assets_list], indent=2)

        except json.JSONDecodeError as e:
            error_msg = f"Error: Invalid JSON format for social_media_schedule_json: {str(e)}"
            logger.error(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"Error generating images for schedule: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg

    def _generate_image_prompt(
        self,
        item: ScheduleItem,
    ) -> str:
        """
        Generate a detailed image prompt based on schedule item context.
        
        Args:
            item: ScheduleItem object
            
        Returns:
            Image generation prompt string, or error message
        """
        try:
            # Create LLM with structured output for prompt generation
            llm = LLM(
                model=general_llm.model,
                response_format=ImagePromptOutput,
                temperature=0.7,
            )

            prompt_template = f"""You are an expert visual content creator specializing in Instagram marketing imagery. Generate a detailed, high-quality image generation prompt for the following schedule item.

**Schedule Item Details:**
- ID: {item.id}
- Phase: {item.phase_name or 'N/A'}
- Week: {item.week or 'N/A'}
- Date: {item.date}
- Post Type: {item.post_type}
- Theme/Concept: {item.theme_concept}
- Objective: {item.objective}
- Description: {item.description}

**Requirements:**
1. Create a detailed, vivid image prompt that:
   - Aligns with the theme_concept and description
   - Supports the post's objective
   - Is appropriate for Instagram ({item.post_type} format)
   - Is visually compelling and engaging

2. The prompt should be:
   - Specific and detailed (include composition, lighting, mood, colors, style)
   - Professional and production-ready
   - Optimized for Instagram's visual format
   - Between 50-150 words

3. Consider the post_type:
   - POST: Can be more detailed, landscape or square format
   - STORY: Should be vertical/portrait format, eye-catching, simple composition

**CRITICAL REQUIREMENTS:**
- Generate ONLY the image prompt text - no explanations, no meta-commentary
- The prompt should be ready to use directly with an image generation AI
- Focus on visual elements, composition, mood, and style
- Base the prompt entirely on the schedule item's theme_concept, description, and objective
- **NO TEXT IN IMAGE:** The image must NOT contain any text, words, letters, numbers, or written content. These images will be used in poster renders where text will be added separately.
- **VISUAL ONLY:** The prompt should describe only visual elements - no quotes, slogans, captions, or text overlays
- Explicitly include in your prompt: "no text", "no words", "no letters", "visual only", "text-free"
"""

            # Generate prompt using LLM
            try:
                response = llm.call(prompt_template)
            except Exception as llm_error:
                error_msg = f"Error: LLM call failed for item {item.id}: {str(llm_error)}"
                logger.error(error_msg, exc_info=True)
                return error_msg

            # Parse response
            try:
                if isinstance(response, str):
                    prompt_output = ImagePromptOutput.model_validate_json(response)
                elif isinstance(response, dict):
                    prompt_output = ImagePromptOutput.model_validate(response)
                elif hasattr(response, 'prompt'):
                    # Handle case where response is already a Pydantic model instance
                    prompt_output = response
                else:
                    error_msg = f"Error: Unexpected response type for item {item.id}: {type(response)}. Response: {str(response)[:200]}"
                    logger.error(error_msg)
                    return error_msg
            except Exception as parse_error:
                error_msg = f"Error: Failed to parse LLM response for item {item.id}: {str(parse_error)}. Response: {str(response)[:200]}"
                logger.error(error_msg, exc_info=True)
                return error_msg

            # Validate prompt is not empty
            if not hasattr(prompt_output, 'prompt') or not prompt_output.prompt or not prompt_output.prompt.strip():
                error_msg = f"Error: Generated prompt for item {item.id} is empty."
                logger.error(error_msg)
                return error_msg

            logger.info(f"Generated image prompt for item {item.id}: {prompt_output.prompt[:100]}...")
            return prompt_output.prompt

        except Exception as e:
            error_msg = f"Error generating image prompt for item {item.id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg


# Export a ready-to-use instance of the tool
generate_images_for_schedule_tool = GenerateImagesForScheduleTool()

