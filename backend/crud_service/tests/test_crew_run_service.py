import asyncio
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

sys.modules.setdefault("boto3", MagicMock())

config_stub = ModuleType("config")
config_stub.settings = SimpleNamespace(
    INTERNAL_CREW_API_KEY="test-key",
    CREW_SERVICE_URL="http://crew-service",
    CRUD_DATABASE_URL="postgresql://user:pass@localhost:5432/db",
    DB_HOST="localhost",
    DB_PORT="5432",
    DB_NAME="db",
    DB_USER="user",
    DB_PASSWORD="pass",
    JWKS_URL="http://example.com/jwks",
    COGNITO_REGION="us-east-1",
    COGNITO_USER_POOL_ID="pool",
    COGNITO_APP_CLIENT_ID="client",
    S3_BUCKET_NAME="bucket",
    S3_REGION="us-east-1",
    AWS_ACCESS_KEY_ID="key",
    AWS_SECRET_ACCESS_KEY="secret",
)
sys.modules.setdefault("config", config_stub)

db_connection_stub = ModuleType("app.db.connection")


async def _dummy_test_connection():
    return None


async def _dummy_get_session():
    yield MagicMock(name="session")


db_connection_stub.test_connection = _dummy_test_connection
db_connection_stub.get_session = _dummy_get_session
sys.modules.setdefault("app.db.connection", db_connection_stub)

botocore_stub = ModuleType("botocore")
botocore_client_stub = ModuleType("botocore.client")
botocore_client_stub.BaseClient = object
sys.modules.setdefault("botocore", botocore_stub)
sys.modules.setdefault("botocore.client", botocore_client_stub)

jose_stub = ModuleType("jose")


class _DummyJWTError(Exception):
    pass


jose_stub.JWTError = _DummyJWTError
jose_stub.jwt = SimpleNamespace(
    get_unverified_header=lambda token: {"kid": "dummy"},
    decode=lambda token,
    rsa_key,
    algorithms=None,
    audience=None,
    issuer=None,
    options=None: {"sub": "00000000-0000-0000-0000-000000000000"},
)

sys.modules.setdefault("jose", jose_stub)

from app.api.crew_client.models.task_info import TaskInfo as CrewTaskInfo
from app.models.models import TaskRead
from app.services.crew_run_service import CrewRunService


def test_get_task_snapshot_includes_full_task_payload(monkeypatch):
    service = CrewRunService(
        crew_service=MagicMock(),
        repository=MagicMock(),
        queue_repository=MagicMock(),
        session=MagicMock(),
    )

    task_definition = {
        "key": "research_task",
        "name": "Research Task",
        "task_description": "Plan the research scope",
        "description": "Detailed research instructions",
        "expected_output": "Research summary",
        "agent": "researcher",
        "output_file": "research.md",
        "reads": [{"field": "topic", "cardinality": "ONE"}],
        "writes": [{"field": "research_summary", "mode": "REPLACE"}],
        "crew_inputs": "topic",
    }
    remote_task = CrewTaskInfo.from_dict(task_definition)

    fake_get_tasks = SimpleNamespace(asyncio=AsyncMock(return_value=[remote_task]))
    monkeypatch.setattr(
        "app.services.crew_run_service.get_pre_defined_tasks",
        fake_get_tasks,
    )

    tasks = [TaskRead(id=uuid4(), key=task_definition["key"], order=1)]

    snapshot = asyncio.run(service._get_tasks_snapshot(tasks))

    assert len(snapshot) == 1
    snapshot_task = snapshot[0]
    assert snapshot_task.description == task_definition["description"]
    assert snapshot_task.expected_output == task_definition["expected_output"]
    assert snapshot_task.agent == task_definition["agent"]
    assert snapshot_task.output_file == task_definition["output_file"]
    assert snapshot_task.reads[0].field == task_definition["reads"][0]["field"]
    assert snapshot_task.writes[0].mode == task_definition["writes"][0]["mode"]
    assert snapshot_task.crew_inputs == task_definition["crew_inputs"]
