"""Structured logging utility for microservices."""
import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict


class JSONLogFormatter(logging.Formatter):
    """Formats logs as JSON lines for ingestion into observability stacks."""
    def __init__(self, service_name: str = "service"):
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": self.service_name,
            "logger": record.name,
            "message": record.getMessage(),
            "line": f"{record.filename}:{record.lineno}",
        }
        if hasattr(record, "correlation_id"):
            log_data["correlation_id"] = record.correlation_id
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)


def setup_logger(service_name: str, log_level: str = "INFO", log_format: str = "json") -> logging.Logger:
    """Configures and returns a logger instance."""
    logger = logging.getLogger(service_name)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Avoid duplicate handlers
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        if log_format.lower() == "json":
            handler.setFormatter(JSONLogFormatter(service_name=service_name))
        else:
            handler.setFormatter(logging.Formatter(
                "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
            ))
        logger.addHandler(handler)
        logger.propagate = False
        
    return logger

