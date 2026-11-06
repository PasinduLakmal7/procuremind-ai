import os
import sys
from pathlib import Path
from pydantic import Field

# Ensure root directory is on PYTHONPATH for shared imports
root_path = str(Path(__file__).resolve().parents[4])
if root_path not in sys.path:
    sys.path.insert(0, root_path)

from shared.core.config import MicroserviceBaseSettings


class IdentitySettings(MicroserviceBaseSettings):
    """Configuration settings specific to Identity Service."""
    APP_NAME: str = "identity-service"
    PORT: int = 8001
    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/identity_db",
        description="Database URL for identity_db"
    )
    # Auth Rate limiting
    AUTH_RATE_LIMIT_PER_MINUTE: int = Field(default=10, description="Max login attempts per minute per IP")


settings = IdentitySettings()

