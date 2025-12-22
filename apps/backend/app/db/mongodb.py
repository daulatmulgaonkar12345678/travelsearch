from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class MongoDB:
    client: AsyncIOMotorClient | None = None
    db = None


mongodb = MongoDB()


async def connect_db():
    """Connect to MongoDB"""
    try:
        # ✅ Strip to avoid newline / whitespace issues from env vars
        mongodb_uri = settings.mongodb_uri.strip()

        mongodb.client = AsyncIOMotorClient(
            mongodb_uri,
            serverSelectionTimeoutMS=5000,  # fail fast if unreachable
        )

        # If DB name is in URI, this works correctly
        mongodb.db = mongodb.client.get_default_database()

        # ✅ Test connection
        await mongodb.client.admin.command("ping")

        logger.info("✅ Connected to MongoDB successfully")

    except Exception as e:
        logger.exception("❌ Failed to connect to MongoDB")
        raise e


async def close_db():
    """Close MongoDB connection"""
    if mongodb.client:
        mongodb.client.close()
        logger.info("🔒 Closed MongoDB connection")


def get_db():
    """Get database instance (sync usage)"""
    if mongodb.db is None:
        raise RuntimeError("MongoDB is not connected")
    return mongodb.db


async def get_database():
    """Get database instance (async usage)"""
    if mongodb.db is None:
        raise RuntimeError("MongoDB is not connected")
    return mongodb.db


# ======================
# Collections
# ======================

def get_users_collection():
    return get_db()["users"]


def get_seo_pages_collection():
    return get_db()["seo_pages"]


def get_clicks_collection():
    return get_db()["clicks"]


def get_providers_collection():
    return get_db()["providers"]


def get_admin_audit_collection():
    return get_db()["admin_audit"]


def get_price_alerts_collection():
    return get_db()["price_alerts"]
