"""Main entry point for the Multi-Protocol Agent Orchestrator"""

import asyncio
import sys
from pathlib import Path

import structlog
import uvicorn

from .config import get_settings

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


def main():
    """Main entry point"""
    settings = get_settings()
    
    # Set up logging level
    import logging
    logging.basicConfig(level=getattr(logging, settings.log_level))
    
    logger.info(
        "Starting Multi-Protocol Agent Orchestrator",
        version=settings.app_version,
        environment=settings.environment,
        host=settings.host,
        port=settings.port
    )
    
    # Run the FastAPI application
    uvicorn.run(
        "orchestrator.api:app",
        host=settings.host,
        port=settings.port,
        workers=settings.workers if settings.environment == "production" else 1,
        log_level=settings.log_level.lower(),
        reload=settings.debug,
        access_log=True,
        server_header=False,
        date_header=False
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Shutting down orchestrator...")
        sys.exit(0)
    except Exception as e:
        logger.error("Failed to start orchestrator", error=str(e))
        sys.exit(1)