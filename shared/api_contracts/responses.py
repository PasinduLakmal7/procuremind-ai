"""Standard API response schemas and envelopes."""
from datetime import datetime, timezone
from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error description")
    details: Optional[Any] = Field(default=None, description="Detailed error information or field validations")
    request_id: Optional[str] = Field(default=None, description="Correlation or request identifier")


class ErrorResponse(BaseModel):
    success: bool = Field(default=False)
    error: ErrorDetail
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ApiResponse(BaseModel, Generic[T]):
    success: bool = Field(default=True)
    data: T
    message: Optional[str] = Field(default=None)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class HealthResponse(BaseModel):
    status: str = Field(default="ok", description="Health status (ok, degraded, down)")
    service: str = Field(..., description="Service name")
    version: str = Field(default="0.1.0", description="Service semantic version")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    database: Optional[str] = Field(default=None, description="Database status (connected, disconnected, n/a)")

