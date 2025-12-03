import os
import json
import requests
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type

from app.api.crud_client.models.artifact_type import ArtifactType
from app.lib.tools.utils.artifact import get_default_artifact_service

ORSHOT_API_KEY = os.getenv("ORSHOT_API_KEY")
ORSHOT_API_URL = os.getenv("ORSHOT_API_URL", "https://api.orshot.com/v1/studio/render")
ORSHOT_MOCK_MODE = os.getenv("ORSHOT_MOCK_MODE", "false").lower() == "true"

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
            if ORSHOT_MOCK_MODE:
                print(f"\n[MOCK ORSHOT] Skipping API Call for Template {templateId}")
                print(f"[MOCK ORSHOT] Generated Modifications:\n{json.dumps(modifications, indent=2)}")
                
                # Return a dummy placeholder image URL so the batch tool continues successfully
                return "https://placehold.co/1080x1080/png?text=Mock+Orshot+Render"
            
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

            response = requests.post(
                ORSHOT_API_URL, 
                json=orshot_payload, 
                headers=headers, 
                timeout=30
            )
            if not response.ok:
                try:
                    error_details = response.json()
                except Exception:
                    error_details = response.text

                return f"Error: Orshot API failed (Status {response.status_code}). Reason: {error_details}"

            data = response.json()

            if "data" in data and isinstance(data["data"], dict):
                base64_content = data["data"].get("content")
            else:
                base64_content = data.get("result") or data.get("base64") or data.get("content")
            
            if not base64_content:
                return f"Error: Could not find base64 data. Response keys: {list(data.keys())}"

            if "," in base64_content:
                base64_content = base64_content.split(",")[1]

            artifact_service = get_default_artifact_service()
            save_result = artifact_service.save_artifact(
                crew_run_id=crew_run_id,
                file_name=f"orshot_render_{templateId}.png",
                file_content_base64=base64_content,
                artifact_type=ArtifactType.IMAGE,
            )
            if not save_result.is_success or not save_result.artifact:
                return save_result.error or "Error: Error saving artifact to CRUD service."

            s3_result = artifact_service.get_artifact_s3_url(
                artifact_id=save_result.artifact.id,
                crew_run_id=crew_run_id,
            )
            if not s3_result.is_success or not s3_result.url:
                return s3_result.error or "Error: Error obtaining S3 URL from artifact."

            return s3_result.url

        except Exception as e:
            return f"Error: Error executing Orshot render: {str(e)}"


orshot_render_tool = OrshotRenderTool()
