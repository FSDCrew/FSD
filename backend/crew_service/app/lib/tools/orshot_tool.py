import json
import os
import requests
import time
from crewai.tools import tool

# Ensure these are set in your .env file
ORSHOT_API_KEY = os.getenv("ORSHOT_API_KEY")
ORSHOT_API_URL = os.getenv("ORSHOT_API_URL", "https://api.orshot.com/v1/studio/render")

@tool("orshot_render_tool")
def orshot_render_tool(payload: str):
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
        # Ensure payload is valid JSON before sending
        if isinstance(payload, str):
            json_payload = json.loads(payload)
        else:
            json_payload = payload

        json_payload["response"] = {
            "type": "base64",
            "format": "png",
            "scale": 1
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {ORSHOT_API_KEY}"
        }

        # Send to Orshot
        response = requests.post(
            ORSHOT_API_URL, 
            json=json_payload, 
            headers=headers, 
            timeout=30
        )
        response.raise_for_status()

        data = response.json()
        
        # Return base64 content of rendered image
        return data.get("content")

    except Exception as e:
        return f"Error executing Orshot render: {str(e)}"