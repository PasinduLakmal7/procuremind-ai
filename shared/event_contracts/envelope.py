"""Standard integration event envelope and metadata."""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Generic, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class EventEnvelope(BaseModel, Generic[T]):
    """Standard cloud-event style envelope for integration messaging."""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = Field(..., description="Fully qualified event type name, e.g. identity.user_registered.v1")
    producer: str = Field(..., description="Name of the service that generated the event")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    correlation_id: Optional[str] = Field(default=None, description="Distributed correlation ID")
    schema_version: str = Field(default="1.0", description="Event contract schema version")
    payload: T
    metadata: Dict[str, Any] = Field(default_factory=dict)

