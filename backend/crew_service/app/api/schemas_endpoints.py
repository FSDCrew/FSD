from fastapi import APIRouter, Depends
from app.dependencies import get_user_token
from app.models.models import CustomTypesResponse

schemas_router = APIRouter(
    prefix="/schemas",
    tags=["schemas"],
)


@schemas_router.get(
    "/",
    response_model=CustomTypesResponse,
    include_in_schema=True,
    summary="Get Custom Type Schemas",
    description="Exposes custom types in OpenAPI schema for client generation. Returns empty object. This endpoint ensures all custom types (MarketingResearch, ContentStrategy, SocialMediaSchedule, OrshotSchemaField, AllowedTemplateId, OrshotDataType) appear in the OpenAPI schema so tools like openapi-ts can generate TypeScript types."
)
async def get_custom_type_schemas(
    user_token: str = Depends(get_user_token),
) -> CustomTypesResponse:
    """
    Get custom type schemas for OpenAPI client generation.
    
    This endpoint exists solely to expose custom types in the OpenAPI schema.
    It returns an empty CustomTypesResponse instance. The actual schemas are
    available in the OpenAPI JSON schema components.
    """
    return CustomTypesResponse()