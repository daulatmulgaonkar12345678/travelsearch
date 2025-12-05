"""
Bridge file to import the monorepo backend application.
This file is required by supervisor config and imports the actual app from /app/apps/backend
"""
import sys
from pathlib import Path

# Add the monorepo backend to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "backend"))

# Import the actual FastAPI app from the monorepo
from app.main import app

__all__ = ["app"]