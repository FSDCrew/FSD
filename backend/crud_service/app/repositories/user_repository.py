from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.schemas.schemas import User as UserDB
from app.models.models import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_user_by_id(self, user_id: UUID) -> User | None:
        """Get a user from the database by ID."""
        query = select(UserDB).where(UserDB.id == user_id)
        result = await self.session.execute(query)
        db_user = result.scalar_one_or_none()
        if not db_user:
            return None
        
        picture_value = str(db_user.picture) if db_user.picture is not None else None
        return User(
            id=UUID(str(db_user.id)),
            email=str(db_user.email),
            name=f"{db_user.given_name} {db_user.family_name}",
            given_name=str(db_user.given_name),
            family_name=str(db_user.family_name),
            picture=picture_value
        )
    
    async def create_user(
        self,
        user_id: UUID,
        email: str,
        given_name: str,
        family_name: str,
        picture: str | None = None
    ) -> User:
        """Create a new user in the database."""
        db_user = UserDB(
            id=user_id,
            email=email,
            given_name=given_name,
            family_name=family_name,
            picture=picture
        )
        self.session.add(db_user)
        await self.session.commit()
        await self.session.refresh(db_user)
        
        picture_value = str(db_user.picture) if db_user.picture is not None else None
        return User(
            id=UUID(str(db_user.id)),
            email=str(db_user.email),
            name=f"{db_user.given_name} {db_user.family_name}",
            given_name=str(db_user.given_name),
            family_name=str(db_user.family_name),
            picture=picture_value
        )
