import base64
import requests
from typing import Type
from uuid import UUID
from openai import OpenAI

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from app.api.crud_client.models.artifact_type import ArtifactType
from app.lib.tools.utils.artifact import get_default_artifact_service
from config import settings

class GenerateImageInput(BaseModel):
    prompt: str = Field(..., description="A detailed description of the image to generate.")
    crew_run_id: str = Field(..., description="The UUID of the current crew run.")

class GenerateImageTool(BaseTool):
    name: str = "generate_image_tool"
    description: str = (
        "Generates an image using AI (DALL-E 3), saves it as an artifact, and returns the persistent S3 URL. "
        "Useful for creating visual assets when none exist."
    )
    args_schema: Type[BaseModel] = GenerateImageInput

    def _run(self, prompt: str, crew_run_id: str) -> str:
        try:
            
            print(f"Generating image for prompt: {prompt[:50]}...")
            
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            
            response = client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )

            if response is None or not response.data or len(response.data) == 0:
                return "Error: No image data returned from OpenAI."
            
            temp_url = response.data[0].url
            if not temp_url:
                return "Error: OpenAI returned no image URL."


            image_response = requests.get(temp_url)
            image_response.raise_for_status()
            
            base64_content = base64.b64encode(image_response.content).decode('utf-8')


            print(f"Saving Image Artifact for Run: {crew_run_id}...")
            artifact_service = get_default_artifact_service()
            safe_name = "".join(x for x in prompt[:20] if x.isalnum()) or "image"
            file_name = f"gen_{safe_name}_{UUID(crew_run_id).hex[:8]}.png"

            save_result = artifact_service.save_artifact(
                crew_run_id=crew_run_id,
                file_name=file_name,
                file_content_base64=base64_content,
                artifact_type=ArtifactType.IMAGE,
            )
            if not save_result.is_success or not save_result.artifact:
                return save_result.error or "Error saving artifact to CRUD service."

            s3_result = artifact_service.get_artifact_s3_url(
                artifact_id=save_result.artifact.id,
                crew_run_id=crew_run_id,
            )
            if not s3_result.is_success or not s3_result.url:
                return s3_result.error or "Error obtaining artifact S3 URL."

            return s3_result.url

        except Exception as e:
            return f"Error creating image: {str(e)}"

generate_image_tool = GenerateImageTool()
