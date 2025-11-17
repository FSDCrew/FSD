from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.schemas.schemas import Artifact as ArtifactDB, CrewRun as CrewRunDB, Crew as CrewDB
from app.models.models import ArtifactRead, ArtifactType, ArtifactCreate

class ArtifactRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_artifact(self, artifact: ArtifactCreate, crew_run_id: UUID) -> ArtifactDB:
        """
        Creates a new artifact in the database, linked to a crew run.
        The artifact data is expected to contain object_key and file_name 
        (populated by the ArtifactService after S3 upload).
        """
        db_artifact = ArtifactDB(
            crew_run_id=crew_run_id,
            type=ArtifactType(artifact.type.value),
            object_key=artifact.object_key,
            file_name=artifact.file_name
        )
        self.session.add(db_artifact)
        await self.session.commit()
        await self.session.refresh(db_artifact)
        return db_artifact

    async def get_artifact(self, artifact_id: UUID) -> ArtifactDB | None:
        """Retrieve an artifact by its ID."""
        query = select(ArtifactDB).where(ArtifactDB.id == artifact_id)
        result = await self.session.execute(query)
        db_artifact = result.scalar_one_or_none()
        return db_artifact