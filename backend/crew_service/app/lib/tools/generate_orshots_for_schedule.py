import json
import logging
import os
from typing import List, Type, Dict, Optional

from crewai import LLM
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

# Import your existing single-item tool to reuse the API logic
from app.lib.tools.orshot_tool import orshot_render_tool
from app.lib.tools.imagen_generator import generate_imagen_tool
from app.lib.tools.utils.validate import validate_custom_type
from app.models.models import ScheduleItem, ImageAsset, OrshotRender
from app.services.flow.llm_registry import general_llm

logger = logging.getLogger(__name__)

# Note: We don't use structured output for modifications because OpenAI doesn't support Dict[str, str]
# Instead, we'll parse the JSON response manually

class GenerateOrshotsForScheduleInput(BaseModel):
    social_media_schedule_json: str = Field(..., description="The SocialMediaSchedule object in JSON format")
    image_assets_json: str = Field(..., description="The list of ImageAsset objects in JSON format")
    template_id: int = Field(..., description="The Orshot Template ID to use")
    orshot_schema_json: str = Field(..., description="The JSON schema definitions for the template fields")
    crew_run_id: str = Field(..., description="The UUID of the current crew run")

class GenerateOrshotsForScheduleTool(BaseTool):
    name: str = "generate_orshots_for_schedule"
    description: str = (
        "Generates Orshot renders for ALL items in a schedule automatically. "
        "Iterates through the schedule, maps text content using AI, injects generated images, "
        "and returns a list of S3 URLs."
    )
    args_schema: Type[BaseModel] = GenerateOrshotsForScheduleInput

    def _run(self, social_media_schedule_json: str, image_assets_json: str, template_id: int, orshot_schema_json: str, crew_run_id: str) -> str:
        """
        Generate Orshot renders for all items in a social media schedule.
        
        Implements intelligent asset management:
        - Uses existing images from image_assets when available
        - Generates new images on-the-fly when needed
        - Handles errors gracefully to prevent batch failures
        """
        try:
            # ====================================================================
            # 1. PARSE INPUTS
            # ====================================================================
            
            # 1.1 Parse and normalize schedule JSON
            json_string = None
            if isinstance(social_media_schedule_json, str):
                try:
                    parsed = json.loads(social_media_schedule_json)
                    # Normalize date and post_type values for Pydantic validation
                    for item in parsed.get('items', []):
                        if 'date' in item and isinstance(item['date'], str) and 'T' in item['date']:
                            item['date'] = item['date'].split('T')[0]  # Extract date part from ISO datetime
                        if 'post_type' in item and isinstance(item['post_type'], str):
                            item['post_type'] = item['post_type'].upper()  # Normalize to enum values
                    json_string = json.dumps(parsed)
                except json.JSONDecodeError as json_err:
                    error_msg = f"Error: Invalid JSON format in social_media_schedule_json: {str(json_err)}"
                    logger.error(error_msg)
                    return error_msg
            elif isinstance(social_media_schedule_json, dict):
                # Normalize dict values
                for item in social_media_schedule_json.get('items', []):
                    if 'date' in item and isinstance(item['date'], str) and 'T' in item['date']:
                        item['date'] = item['date'].split('T')[0]
                    if 'post_type' in item and isinstance(item['post_type'], str):
                        item['post_type'] = item['post_type'].upper()
                json_string = json.dumps(social_media_schedule_json)
            else:
                return "Error: social_media_schedule_json must be a JSON string or dict"

            # Validate schedule using Pydantic model
            schedule_data = validate_custom_type("SocialMediaSchedule", json_string, strict=True)
            
            if not schedule_data.items or len(schedule_data.items) == 0:
                error_msg = "Error: Social media schedule contains no items."
                logger.error(error_msg)
                return error_msg

            # 1.2 Parse image assets (handle empty/null cases safely)
            image_assets: List[ImageAsset] = []
            if image_assets_json and image_assets_json.strip():
                try:
                    raw_assets = json.loads(image_assets_json) if isinstance(image_assets_json, str) else image_assets_json
                    if raw_assets and isinstance(raw_assets, list) and len(raw_assets) > 0:
                        image_assets = [ImageAsset(**asset) for asset in raw_assets]
                        logger.info(f"Parsed {len(image_assets)} image assets from input")
                except Exception as e:
                    logger.warning(f"Could not parse image assets: {e}. Will generate images as needed.")
                    image_assets = []  # Ensure it's an empty list
            else:
                logger.info("No image_assets_json provided or empty - will generate images as needed")

            # 1.3 Parse schema to determine if template requires images
            image_field_names: List[str] = []
            try:
                schema_data = json.loads(orshot_schema_json) if isinstance(orshot_schema_json, str) else orshot_schema_json
                if isinstance(schema_data, list):
                    for field_def in schema_data:
                        if isinstance(field_def, dict) and field_def.get("dataType") == "IMAGE":
                            field_name = field_def.get("field", "image")
                            image_field_names.append(field_name)
                    logger.info(f"Schema requires images in fields: {image_field_names}")
            except Exception as e:
                logger.warning(f"Could not parse schema to find image fields: {e}. Assuming no image fields.")
                image_field_names = []

            # ====================================================================
            # 2. ITERATE SCHEDULE ITEMS
            # ====================================================================
            
            logger.info(f"Processing {len(schedule_data.items)} schedule items for Orshot renders (crew run {crew_run_id})")
            orshot_renders_list: List[OrshotRender] = []
            
            for item in schedule_data.items:
                try:
                    logger.info(f"Processing Orshot render for schedule item {item.id}")
                    
                    # --------------------------------------------------------------------
                    # A. GENERATE TEXT MODIFICATIONS
                    # --------------------------------------------------------------------
                    text_modifications = self._generate_text_modifications(
                        item, 
                        orshot_schema_json, 
                        exclude_image_fields=True
                    )
                    
                    if not text_modifications:
                        logger.warning(f"Failed to generate text modifications for item {item.id}, using empty dict")
                        text_modifications = {}
                    
                    # Start with text modifications as the base payload
                    modifications = {**text_modifications}
                    
                    # --------------------------------------------------------------------
                    # B. HANDLE IMAGE (CONDITIONAL)
                    # --------------------------------------------------------------------
                    
                    # Check if schema requires an image
                    requires_image = len(image_field_names) > 0
                    
                    if requires_image:
                        # Look for matching image asset by schedule_item_id
                        matching_image = next(
                            (img for img in image_assets if img.schedule_item_id == item.id), 
                            None
                        )
                        
                        image_url = None
                        
                        if matching_image and matching_image.image_url:
                            # Use existing image from image_assets
                            image_url = matching_image.image_url
                            logger.info(f"Using existing image for item {item.id}: {image_url[:50]}...")
                        else:
                            # Fallback: Generate new image on-the-fly
                            logger.info(f"No matching image found for item {item.id}, generating new image...")
                            
                            # Generate descriptive image prompt based on schedule item
                            image_prompt = self._generate_image_prompt(item)
                            
                            if image_prompt.startswith("Error:"):
                                logger.error(f"Failed to generate image prompt for item {item.id}: {image_prompt}")
                                # Continue without image - Orshot may handle missing image
                            else:
                                # Call generate_imagen_tool (returns S3 URL, saves artifact automatically)
                                logger.info(f"Calling generate_imagen_tool for item {item.id} (crew_run_id: {crew_run_id})")
                                image_url = generate_imagen_tool._run(
                                    prompt=image_prompt,
                                    crew_run_id=crew_run_id
                                )
                                
                                if image_url.startswith("Error:"):
                                    logger.error(f"Failed to generate image for item {item.id}: {image_url}")
                                    image_url = None  # Clear the error string
                                else:
                                    logger.info(f"Successfully generated and saved image artifact for item {item.id}: {image_url[:50]}...")
                                    
                                    # Cache the generated image for potential reuse
                                    new_image_asset = ImageAsset(
                                        schedule_item_id=item.id,
                                        image_url=image_url
                                    )
                                    image_assets.append(new_image_asset)
                        
                        # Inject image URL into modifications (map to all image field keys)
                        if image_url:
                            for field_name in image_field_names:
                                modifications[field_name] = image_url
                                logger.debug(f"Injected image URL into field '{field_name}' for item {item.id}")
                        else:
                            logger.warning(f"Image required but not available for item {item.id} - Orshot may fail or use placeholder")
                    
                    # --------------------------------------------------------------------
                    # C. RENDER & SAVE
                    # --------------------------------------------------------------------
                    
                    logger.info(f"Calling orshot_render_tool for item {item.id} (template_id: {template_id}, crew_run_id: {crew_run_id})")
                    logger.debug(f"Modifications payload: {json.dumps(modifications, indent=2)}")
                    
                    # Call orshot_render_tool (handles API call and saves render to S3/Artifacts automatically)
                    render_url = orshot_render_tool._run(
                        templateId=template_id,
                        modifications=modifications,
                        crew_run_id=crew_run_id
                    )
                    
                    if render_url.startswith("Error:"):
                        logger.error(f"Failed render for item {item.id}: {render_url}")
                        # Continue with next item instead of failing completely
                        continue
                    
                    logger.info(f"Successfully generated and saved Orshot render artifact for item {item.id}: {render_url[:50]}...")
                    
                    # --------------------------------------------------------------------
                    # D. COLLECT OUTPUT
                    # --------------------------------------------------------------------
                    
                    # Create OrshotRender object with schedule_item_id and render_url
                    orshot_render = OrshotRender(
                        schedule_item_id=item.id,
                        render_url=render_url
                    )
                    orshot_renders_list.append(orshot_render)
                    
                except Exception as item_error:
                    # Robust error handling: one failure doesn't crash the whole batch
                    logger.error(f"Error processing schedule item {item.id}: {str(item_error)}", exc_info=True)
                    logger.warning(f"Skipping item {item.id} and continuing with next item")
                    continue
            
            # ====================================================================
            # 3. RETURN RESULTS
            # ====================================================================
            
            if len(orshot_renders_list) == 0:
                error_msg = "Error: Failed to generate any Orshot renders. All render attempts failed."
                logger.error(error_msg)
                return error_msg

            logger.info(f"Successfully generated {len(orshot_renders_list)} Orshot renders out of {len(schedule_data.items)} items")
            
            # Return JSON array string (list of OrshotRender objects)
            return json.dumps([render.model_dump() for render in orshot_renders_list], indent=2)

        except json.JSONDecodeError as e:
            error_msg = f"Error: Invalid JSON format for social_media_schedule_json: {str(e)}"
            logger.error(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"Error executing batch orshot render: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg

    def _generate_text_modifications(self, item: ScheduleItem, schema_json: str, exclude_image_fields: bool = False) -> Dict[str, str]:
        """Uses LLM to map schedule item details to the specific template text fields."""
        try:
            # Don't use structured output - OpenAI doesn't support Dict[str, str]
            # Parse JSON response manually instead
            llm = LLM(model=general_llm.model, temperature=0.7)
            
            # Filter schema to exclude image fields if requested
            schema_data = None
            filtered_schema = schema_json
            if exclude_image_fields:
                try:
                    schema_data = json.loads(schema_json) if isinstance(schema_json, str) else schema_json
                    if isinstance(schema_data, list):
                        # Filter out IMAGE type fields
                        text_only_schema = [field for field in schema_data if isinstance(field, dict) and field.get("dataType") != "IMAGE"]
                        filtered_schema = json.dumps(text_only_schema, indent=2)
                except Exception as e:
                    logger.warning(f"Could not filter schema: {e}, using full schema")
                    filtered_schema = schema_json
            
            prompt = f"""
            Map the following Social Media Post content to the provided Design Template Fields.
            
            **Post Details:**
            - Theme: {item.theme_concept}
            - Objective: {item.objective}
            - Description: {item.description}
            - Date: {item.date}
            
            **Template Schema (Target Fields - TEXT and BACKGROUND only):**
            {filtered_schema}
            
            **CRITICAL INSTRUCTIONS:**
            1. Generate short, punchy text for the TEXT fields in the schema based on the Post Description.
            2. Generate HEX color codes for BACKGROUND fields based on the theme and description.
            3. Apply CamelCase styling CSS keys if the schema suggests it (e.g. "title.color": "#000000").
            4. **DO NOT include IMAGE fields** - images will be handled separately.
            5. **DO NOT use fake filenames** like "image.jpg" or "product.png" - only include TEXT and BACKGROUND fields.
            6. Return ONLY a valid JSON object with key-value pairs for modifications.
            7. Do NOT include any text before or after the JSON.
            8. The JSON should be a flat object like: {{"mainText": "Your text", "mainText.fontSize": "80px", "backgroundColor": "#000000", ...}}
            
            **Example Output Format (TEXT and BACKGROUND fields only):**
            {{
              "mainText": "Launch Day",
              "mainText.fontSize": "80px",
              "mainTitle": "New Collection",
              "subText1": "Discover our latest designs",
              "backgroundColor": "#000000"
            }}
            
            **REMEMBER:** Do NOT include any image fields in your output. Only TEXT and BACKGROUND fields.
            """
            
            response = llm.call(prompt)
            
            # Parse the JSON response
            if isinstance(response, str):
                # Try to extract JSON from the response
                response_clean = response.strip()
                # Remove markdown code blocks if present
                if response_clean.startswith("```"):
                    # Extract JSON from code block
                    lines = response_clean.split("\n")
                    json_lines = []
                    in_json = False
                    for line in lines:
                        if line.strip().startswith("```"):
                            if not in_json:
                                in_json = True
                            else:
                                break
                        elif in_json:
                            json_lines.append(line)
                    response_clean = "\n".join(json_lines)
                
                try:
                    modifications = json.loads(response_clean)
                    if isinstance(modifications, dict):
                        return modifications
                    else:
                        logger.warning(f"LLM returned non-dict JSON: {type(modifications)}")
                        return {}
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON from LLM response: {e}. Response: {response_clean[:200]}")
                    return {}
            elif isinstance(response, dict):
                return response
            else:
                logger.warning(f"Unexpected response type: {type(response)}")
                return {}
                
        except Exception as e:
            logger.error(f"Error generating text mods: {e}", exc_info=True)
            return {}
    
    def _generate_image_prompt(self, item: ScheduleItem) -> str:
        """Generate a detailed image prompt based on schedule item context."""
        try:
            # Create LLM for prompt generation (no structured output needed)
            llm = LLM(
                model=general_llm.model,
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
- Focus on visual elements, composition, lighting, mood, and style
- Base the prompt entirely on the schedule item's theme_concept, description, and objective

- **STYLE SELECTION:** Based *strictly* on the description and theme, determine if this image should be **Photorealistic** or **Stylized**.
  
  * **CHOOSE PHOTOREALISTIC IF:**
    - The content is about real events (e.g., "Patron's Day", "Concert", "Festival")
    - It features real people, fashion, or specific physical products
    - It describes a specific real-world location (e.g., "Campus Green", "Tokyo Street")
    - *Keywords to use:* "Shot on 35mm", "Depth of field", "Studio lighting", "8k", "Documentary style", "photorealistic", "high-resolution photography", "professional photography", "realistic", "lifelike", "natural lighting", "DSLR quality"
  
  * **CHOOSE STYLIZED/ILLUSTRATION IF:**
    - The content is abstract, conceptual, or educational (e.g., "Tips", "Growth", "Mindset")
    - It describes a mood or vibe without specific physical subjects
    - *Keywords to use:* "3D render", "C4D", "Vibrant vector art", "Minimalist", "Pop art", "illustrated", "stylized", "graphic design", "digital art"

- **NO TEXT IN IMAGE:** The image must NOT contain any text, words, letters, numbers, or written content. These images will be used in poster renders where text will be added separately.
- **VISUAL ONLY:** The prompt should describe only visual elements - no quotes, slogans, captions, or text overlays
- Explicitly include in your prompt: "no text", "no words", "no letters", "visual only", "text-free", plus the appropriate style keywords based on your selection
"""

            # Generate prompt using LLM
            response = llm.call(prompt_template)
            
            # Extract prompt from response (handle both string and structured responses)
            if isinstance(response, str):
                prompt = response.strip()
            elif isinstance(response, dict) and "prompt" in response:
                prompt = response["prompt"]
            else:
                prompt = str(response).strip()
            
            if not prompt or not prompt.strip():
                error_msg = f"Error: Generated prompt for item {item.id} is empty."
                logger.error(error_msg)
                return error_msg

            logger.info(f"Generated image prompt for item {item.id}: {prompt[:100]}...")
            return prompt

        except Exception as e:
            error_msg = f"Error generating image prompt for item {item.id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg

generate_orshots_for_schedule_tool = GenerateOrshotsForScheduleTool()