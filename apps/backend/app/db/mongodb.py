from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class MongoDB:
    client: AsyncIOMotorClient = None
    db = None

mongodb = MongoDB()

async def connect_db():
    """Connect to MongoDB"""
    try:
        mongodb.client = AsyncIOMotorClient(settings.mongodb_uri)
        mongodb.db = mongodb.client.get_database()
        # Test connection
        await mongodb.client.admin.command('ping')
        logger.info("Connected to MongoDB successfully")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise

async def close_db():
    """Close MongoDB connection"""
    if mongodb.client:
        mongodb.client.close()
        logger.info("Closed MongoDB connection")

def get_db():
    """Get database instance"""
    return mongodb.db

async def get_database():
    """Get database instance (async compatible)"""
    return mongodb.db

# Collections
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
