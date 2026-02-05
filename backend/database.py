from motor.motor_asyncio import AsyncIOMotorClient
from config import settings


class Database:
    """MongoDB database connection manager."""
    
    client: AsyncIOMotorClient = None
    
    @classmethod
    async def connect_db(cls):
        """Initialize database connection."""
        cls.client = AsyncIOMotorClient(settings.mongo_uri)
        print(f"Connected to MongoDB at {settings.mongo_uri}")
    
    @classmethod
    async def close_db(cls):
        """Close database connection."""
        if cls.client:
            cls.client.close()
            print("Closed MongoDB connection")
    
    @classmethod
    def get_database(cls):
        """Get the database instance."""
        return cls.client[settings.database_name]


# Convenience function to get database
def get_db():
    """Get database instance."""
    return Database.get_database()