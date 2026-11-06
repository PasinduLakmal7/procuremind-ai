import sys
from pathlib import Path
from pydantic import Field

root_path = str(Path(__file__).resolve().parents[4])
if root_path not in sys.path:
    sys.path.insert(0, root_path)

from shared.core.config import MicroserviceBaseSettings

class ServiceSettings(MicroserviceBaseSettings):
    APP_NAME: str = "risk-service"
    PORT: int = 8006
    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/risk_db",
        description="Database URL for risk_db"
    )

settings = ServiceSettings()
