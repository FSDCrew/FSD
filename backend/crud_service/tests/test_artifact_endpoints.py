import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID
from app.models.models import User, ArtifactRead, ArtifactType
from app.dependencies import get_current_user, get_artifact_service
from app.__init__ import create_app # Assuming this is where your FastAPI app is instantiated


# --- Mock Data ---

MOCK_USER = User(
    id=UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"),
    email="test@example.com",
    name="Test User",
    given_name="Test",
    family_name="User",
    picture=None,
)

MOCK_CREW_RUN_ID = UUID("a0000000-0000-0000-0000-000000000001")
MOCK_ARTIFACT_ID = UUID("123e4567-e89b-12d3-a456-426614174000")

MOCK_ARTIFACT_READ = ArtifactRead(
    id=MOCK_ARTIFACT_ID,
    crew_run_id=MOCK_CREW_RUN_ID,
    type=ArtifactType.TEXT,
    object_key="artifacts/test_user/test_run/test.txt",
    file_name="test-artifact.txt",
)

# --- Mock Dependencies ---

# 1. Mock the user authentication
async def mock_get_current_user():
    """Mocks the user dependency to bypass JWT validation."""
    return MOCK_USER

# 2. Mock the ArtifactService logic
class MockArtifactService:
    """Mocks the service layer to control return values and avoid S3/DB calls."""
    async def create_artifact(self, uploaded_file, artifact_type, crew_run_id, user_id):
        # Simulate successful processing and DB record creation
        assert crew_run_id == MOCK_CREW_RUN_ID
        assert user_id == MOCK_USER.id
        # We ensure the service returns the validated read model
        return MOCK_ARTIFACT_READ

    async def get_artifact(self, artifact_id):
        # Simulate successful retrieval
        return MOCK_ARTIFACT_READ

def mock_get_artifact_service():
    """Dependency override function."""
    return MockArtifactService()

# --- Setup Test Client ---

# Create a TestClient instance for your FastAPI app
app = create_app()

# Override the necessary dependencies for all tests in this module
app.dependency_overrides[get_current_user] = mock_get_current_user
app.dependency_overrides[get_artifact_service] = mock_get_artifact_service
client = TestClient(app)


# --- Test Cases ---

def test_create_artifact_success():
    """Tests a successful artifact upload and database record creation."""
    url = f"/artifact/{MOCK_CREW_RUN_ID}"
    
    # Prepare the file data for multipart/form-data
    file_content = b"This is the content of the artifact."
    
    response = client.post(
        url,
        # FastAPI TestClient correctly handles the 'files' and 'data' separation
        files={
            # The 'file' key must match the 'file: UploadFile = File(...)' parameter name
            "file": ("test_file.txt", file_content, "text/plain")
        },
        data={
            # The 'artifact_type' key must match the 'artifact_type: ArtifactType = Form(...)' parameter name
            "artifact_type": ArtifactType.TEXT.value 
        }
    )

    # 1. Assert Status Code
    assert response.status_code == 201

    # 2. Assert Response Body Structure and Content
    response_data = response.json()
    assert response_data["id"] == str(MOCK_ARTIFACT_ID)
    assert response_data["crew_run_id"] == str(MOCK_CREW_RUN_ID)
    assert response_data["type"] == ArtifactType.TEXT.value
    assert "object_key" in response_data
    assert "file_name" in response_data

def test_create_artifact_missing_file_fails():
    """Tests the endpoint fails when the file content is missing."""
    url = f"/artifact/{MOCK_CREW_RUN_ID}"
    
    response = client.post(
        url,
        data={
            "artifact_type": ArtifactType.TEXT.value 
        }
    )
    
    # FastAPI automatically enforces the required 'file' parameter (422 Unprocessable Entity)
    assert response.status_code == 422 
    assert "detail" in response.json()

def test_get_artifact_success():
    """Tests successful retrieval of an artifact."""
    url = f"/artifact/{MOCK_ARTIFACT_ID}"
    
    response = client.get(url)
    
    # 1. Assert Status Code
    assert response.status_code == 200

    # 2. Assert Response Body Content
    response_data = response.json()
    assert response_data["id"] == str(MOCK_ARTIFACT_ID)