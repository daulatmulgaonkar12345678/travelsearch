from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))

AIRPORTS_FILE = DATA_DIR / "airports-full.json"
HOTEL_CITIES_FILE = DATA_DIR / "hotel-cities.json"
HUB_AIRPORTS_FILE = DATA_DIR / "hub-airports.json"
