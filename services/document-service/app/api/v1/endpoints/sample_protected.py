from fastapi import APIRouter, Depends
from app.core.config import settings
from shared.auth.jwt_validator import get_current_principal_factory, SecurityPrincipal
from shared.api_contracts.responses import ApiResponse

router = APIRouter(prefix="/status", tags=["Status"])

get_current_principal = get_current_principal_factory(
    secret_key=settings.JWT_SECRET_KEY,
    algorithm=settings.JWT_ALGORITHM,
)

@router.get("/summary", response_model=ApiResponse[dict])
def get_service_summary(
    principal: SecurityPrincipal = Depends(get_current_principal),
):
    """Demonstrates cross-service stateless JWT validation and organization isolation."""
    return ApiResponse(
        data={
            "service": "document-service",
            "organization_id": str(principal.organization_id),
            "caller_email": principal.email,
            "roles": principal.roles,
            "message": "Authorized access verified statelessly without querying Identity DB."
        }
    )
