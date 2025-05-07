import databases

DATABASE_URL = "sqlite:///./test.db"  # Replace with your actual database URL

database = databases.Database(DATABASE_URL)

async def connect():
    await database.connect()

async def disconnect():
    await database.disconnect()
