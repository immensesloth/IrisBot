import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

client = AsyncIOMotorClient(MONGO_URI)

db = client["iris"]

warnings = db["warnings"]
settings = db["settings"]
tickets = db["tickets"]
logs = db["logs"]


async def connect_database():
    try:
        await client.admin.command("ping")
        print("✅ Connected to MongoDB!")
    except Exception as e:
        print("❌ MongoDB Connection Failed!")
        print(e)