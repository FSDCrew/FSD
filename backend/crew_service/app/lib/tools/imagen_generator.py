import base64
import logging
from typing import Type
from uuid import UUID
from google import genai
from google.genai import types
from crewai import LLM

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from app.api.crud_client.models.artifact_type import ArtifactType
from app.lib.tools.utils.artifact import get_default_artifact_service
from app.services.flow.llm_registry import general_llm

logger = logging.getLogger(__name__)

class GenerateImagenInput(BaseModel):
    prompt: str = Field(..., description="A detailed description of the image to generate.")
    crew_run_id: str = Field(..., description="The UUID of the current crew run.")

class GenerateImagenTool(BaseTool):
    name: str = "generate_imagen_tool"
    description: str = (
        "Generates an image using Google's Imagen 3 model, saves it as an artifact, and returns the persistent S3 URL. "
        "Useful for creating visual assets when none exist. Automatically retries with safer prompts if blocked by safety filters."
    )
    args_schema: Type[BaseModel] = GenerateImagenInput

    MAX_RETRIES: int = 2  # Maximum number of retry attempts with rewritten prompts

    def _rewrite_prompt_for_safety(self, original_prompt: str, attempt: int) -> str:
        """
        Rewrite a prompt to be safer and more compliant with Gemini safety filters.
        
        Args:
            original_prompt: The original prompt that was blocked
            attempt: The retry attempt number (1-indexed)
            
        Returns:
            A rewritten, safer version of the prompt
        """
        try:
            llm = LLM(
                model=general_llm.model,
                temperature=0.7,
            )
            
            rewrite_instruction = f"""The following image generation prompt was blocked by safety filters. Rewrite it to be safer and more compliant while maintaining the core visual intent.

**Original Prompt (Blocked):**
{original_prompt}

**Your Task:**
Rewrite this prompt to:
1. Remove any potentially sensitive, controversial, or unsafe content
2. Focus on generic, professional, marketing-appropriate imagery
3. Use neutral, positive language
4. Avoid specific people, brands, or controversial topics
5. Keep the visual style and composition intent intact
6. Make it suitable for Instagram marketing content

**Guidelines:**
- If the prompt mentions specific people, replace with generic descriptions (e.g., "person" instead of names)
- If it mentions controversial topics, focus on abstract concepts or neutral visuals
- Keep the artistic style, colors, mood, and composition
- Ensure it's appropriate for social media marketing
- Make it professional and brand-safe

**Return ONLY the rewritten prompt text - no explanations, no meta-commentary.**
"""
            
            rewritten = llm.call(rewrite_instruction)
            
            # Clean up the response (remove markdown code blocks if present)
            if isinstance(rewritten, str):
                rewritten = rewritten.strip()
                if rewritten.startswith("```"):
                    lines = rewritten.split("\n")
                    rewritten = "\n".join(lines[1:-1]) if len(lines) > 2 else rewritten
                rewritten = rewritten.strip()
            
            logger.info(f"Rewritten prompt (attempt {attempt}): {rewritten[:100]}...")
            return rewritten
            
        except Exception as e:
            logger.error(f"Failed to rewrite prompt: {e}")
            # Fallback: return a simplified version
            return f"Professional marketing image: {original_prompt[:100]}"

    def _run(self, prompt: str, crew_run_id: str) -> str:
        """
        Generate image with retry logic for safety filter errors.
        
        Args:
            prompt: Image generation prompt
            crew_run_id: UUID of the current crew run
            
        Returns:
            S3 URL of the generated image, or error message
        """
        current_prompt = prompt
        last_error = None
        
        for attempt in range(self.MAX_RETRIES + 1):  # 0, 1, 2 (total 3 attempts)
            try:
                if attempt > 0:
                    logger.info(f"Retry attempt {attempt} for image generation (rewriting prompt for safety compliance)...")
                    current_prompt = self._rewrite_prompt_for_safety(prompt, attempt)
                
                logger.info(f"Generating image with Imagen 3 (attempt {attempt + 1}/{self.MAX_RETRIES + 1}): {current_prompt[:50]}...")
                
                # Initialize Google Gen AI Client
                # NOTE: Ensure GOOGLE_API_KEY is set in your .env file
                client = genai.Client()
                
                # Generate image using Imagen 3
                response = client.models.generate_images(
                    model='imagen-4.0-generate-001',
                    prompt=current_prompt,
                    config=types.GenerateImagesConfig(
                        number_of_images=1,
                        include_rai_reason=True,
                        output_mime_type="image/png"
                    )
                )

                # Validate response
                if not response.generated_images:
                    error_msg = "Error: No image generated by Google Gen AI (possibly blocked by safety filters)."
                    logger.warning(f"Attempt {attempt + 1} failed: {error_msg}")
                    last_error = error_msg
                    
                    # If this was the last attempt, return error
                    if attempt >= self.MAX_RETRIES:
                        return error_msg
                    # Otherwise, continue to retry with rewritten prompt
                    continue
                    
                first_candidate = response.generated_images[0]

                # Check if the candidate actually contains an image object
                if not first_candidate.image:
                    error_msg = "Error: Candidate returned but 'image' field is None."
                    logger.warning(f"Attempt {attempt + 1} failed: {error_msg}")
                    last_error = error_msg
                    
                    if attempt >= self.MAX_RETRIES:
                        return error_msg
                    continue
                    
                # Imagen returns raw image bytes directly
                image_bytes = first_candidate.image.image_bytes
                if not image_bytes:
                    error_msg = "Error: Generated image bytes are empty."
                    logger.warning(f"Attempt {attempt + 1} failed: {error_msg}")
                    last_error = error_msg
                    
                    if attempt >= self.MAX_RETRIES:
                        return error_msg
                    continue
                    
                # Success! Process and save the image
                base64_content = base64.b64encode(image_bytes).decode('utf-8')

                logger.info(f"Saving Image Artifact for Run: {crew_run_id}...")
                artifact_service = get_default_artifact_service()
                safe_name = "".join(x for x in current_prompt[:20] if x.isalnum()) or "image"
                file_name = f"gen_{safe_name}_{UUID(crew_run_id).hex[:8]}.png"

                save_result = artifact_service.save_artifact(
                    crew_run_id=crew_run_id,
                    file_name=file_name,
                    file_content_base64=base64_content,
                    artifact_type=ArtifactType.IMAGE,
                )
                if not save_result.is_success or not save_result.artifact:
                    error_msg = save_result.error or "Error saving artifact to CRUD service."
                    logger.error(f"Failed to save artifact: {error_msg}")
                    return error_msg

                s3_result = artifact_service.get_artifact_s3_url(
                    artifact_id=save_result.artifact.id,
                    crew_run_id=crew_run_id,
                )
                if not s3_result.is_success or not s3_result.url:
                    error_msg = s3_result.error or "Error obtaining artifact S3 URL."
                    logger.error(f"Failed to get S3 URL: {error_msg}")
                    return error_msg

                logger.info(f"Successfully generated image (attempt {attempt + 1}): {s3_result.url[:50]}...")
                return s3_result.url

            except Exception as e:
                error_msg = f"Error creating image: {str(e)}"
                logger.error(f"Attempt {attempt + 1} failed with exception: {error_msg}", exc_info=True)
                last_error = error_msg
                
                # If this was the last attempt, return error
                if attempt >= self.MAX_RETRIES:
                    return error_msg
                # Otherwise, continue to retry
        
        # If we exhausted all retries, return the last error
        return last_error or "Error: Failed to generate image after all retry attempts."

generate_imagen_tool = GenerateImagenTool()
