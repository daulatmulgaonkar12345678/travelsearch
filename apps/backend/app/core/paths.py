from pathlib import Path
import os

# /app inside Docker, project root locally
BASE_DIR = Path(__file__).resolve().parents[2]

# Data directory (overrideable via ENV)
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
