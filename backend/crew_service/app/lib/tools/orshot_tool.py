import json
import os
import requests
import time
from crewai.tools import tool, BaseTool
from app.api.crud_client import AuthenticatedClient, errors
from uuid import UUID
from pydantic import BaseModel, Field
from typing import Type
from app.api.crud_client.api.artifact import create_artifact_artifact_crew_run_id_post, get_artifact_artifact_artifact_id_get
from app.api.crud_client.models.artifact_server_create import ArtifactServerCreate
from app.api.crud_client.models.artifact_type import ArtifactType
from app.api.crud_client.models.artifact_read import ArtifactRead
# from app.api.crud_client.models.http_validation_error import HTTPValidationError
from config import settings

ORSHOT_API_KEY = os.getenv("ORSHOT_API_KEY")
ORSHOT_API_URL = os.getenv("ORSHOT_API_URL", "https://api.orshot.com/v1/studio/render")
CRUD_SERVICE_URL = os.getenv("CRUD_SERVICE_URL")

class OrshotToolInput(BaseModel):
    templateId: int = Field(..., description="The ID of the Orshot template")
    modifications: dict = Field(..., description="The dictionary of text/image modifications")
    crew_run_id: str = Field(..., description="The UUID of the current crew run")


class OrshotRenderTool(BaseTool):
    name: str = "orshot_render_tool"
    description: str = (
        "Generates an image via Orshot and saves it as an artifact. "
        "Requires templateId, modifications object, and crew_run_id."
    )
    args_schema: Type[BaseModel] = OrshotToolInput

    def _run(self, templateId: int, modifications: dict, crew_run_id: str):
        """
        Sends a pre-constructed JSON payload to the Orshot API to generate a render.
        Payload should contain templateId and modifications as per Orshot API specifications.
        This function will then add the correct response format in base64 PNG.

        Args:
            payload (str): A valid JSON string containing the full request body 
                        (templateId, modifications, etc.) required by Orshot.
                        
        Returns:
            str: The URL of the final rendered image or an error message.
        """
        try:
            # --- STEP 1: Call Orshot API ---
            
            # Construct payload from arguments
            orshot_payload = {
                "templateId": templateId,
                "modifications": modifications,
                "response": {
                    "type": "base64",
                    "format": "png",
                    "scale": 1
                }
            }

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {ORSHOT_API_KEY}"
            }

            # Send to Orshot
            response = requests.post(
                ORSHOT_API_URL, 
                json=orshot_payload, 
                headers=headers, 
                timeout=30
            )
            response.raise_for_status()

            data = response.json()

            if "data" in data and isinstance(data["data"], dict):
                base64_content = data["data"].get("content")
            else:
                # Fallback for other API versions
                base64_content = data.get("result") or data.get("base64") or data.get("content")
            
            if not base64_content:
                return f"Error: Could not find base64 data. Response keys: {list(data.keys())}"

            # --- FIX 2: Strip Data URI Header ---
            # CRUD service uses base64.b64decode which crashes on "data:image/..." headers
            if "," in base64_content:
                base64_content = base64_content.split(",")[1]

            client = AuthenticatedClient(
                base_url=settings.CRUD_SERVICE_URL,
                token=settings.INTERNAL_CREW_API_KEY
            )
            
            artifact_body = ArtifactServerCreate(
                type_=ArtifactType.IMAGE,
                file_name=f"orshot_render_{templateId}.png",
                file_content_base64=base64_content
            )

            create_result = create_artifact_artifact_crew_run_id_post.sync(
                crew_run_id=UUID(crew_run_id),
                client=client,
                body=artifact_body
            )

            if not create_result:
                return "Error saving artifact to CRUD service."
            if isinstance(create_result, ArtifactRead):
                s3_url = get_artifact_artifact_artifact_id_get.sync(
                    artifact_id=create_result.id,
                    client=client
                )
            
            if s3_url:
                return s3_url
            else:
                return "Error obtaining S3 URL from artifact."

            # Return base64 content of rendered image
            # return data.get("content")



        except Exception as e:
            return f"Error executing Orshot render: {str(e)}"


orshot_render_tool = OrshotRenderTool()