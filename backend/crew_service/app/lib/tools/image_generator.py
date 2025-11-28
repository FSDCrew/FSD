import os
import base64
import requests
from typing import Type
from uuid import UUID
from openai import OpenAI

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from app.api.crud_client import AuthenticatedClient
from app.api.crud_client.api.artifact import (
    create_artifact_artifact_crew_run_id_post, 
    get_artifact_artifact_artifact_id_get
)
from app.api.crud_client.models.artifact_server_create import ArtifactServerCreate
from app.api.crud_client.models.artifact_type import ArtifactType
from app.api.crud_client.models.artifact_read import ArtifactRead
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
            
            crud_client = AuthenticatedClient(
                base_url=settings.CRUD_SERVICE_URL,
                token=settings.INTERNAL_CREW_API_KEY
            )

    
            safe_name = "".join(x for x in prompt[:20] if x.isalnum()) or "image"
            file_name = f"gen_{safe_name}_{UUID(crew_run_id).hex[:8]}.png"

            artifact_body = ArtifactServerCreate(
                type_=ArtifactType.IMAGE,
                file_name=file_name,
                file_content_base64=base64_content
            )

            create_result = create_artifact_artifact_crew_run_id_post.sync(
                crew_run_id=UUID(crew_run_id),
                client=crud_client,
                body=artifact_body
            )

            if isinstance(create_result, ArtifactRead):
                s3_url = get_artifact_artifact_artifact_id_get.sync(
                    artifact_id=create_result.id,
                    client=crud_client
                )
                return str(s3_url)
            
            return f"Error saving artifact: {create_result}"

        except Exception as e:
            return f"Error creating image: {str(e)}"

generate_image_tool = GenerateImageTool()

# if __name__ == "__main__":
#     # Simple test
#     test_prompt = "A futuristic city skyline at sunset, with flying cars and neon lights."
#     test_crew_run_id = "c3a8fb27-3fef-4341-a199-9396d8cf34e9"  # Example UUID
#     result = generate_image_tool._run(prompt=test_prompt, crew_run_id=test_crew_run_id)
#     print(f"Result: {result}")