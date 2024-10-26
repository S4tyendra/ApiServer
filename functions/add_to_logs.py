from functions.db import get_database

async def add_to_logs(session:str, email: str, message:str, app:str, timestamp, cost:int = 0):
    db = await get_database()
    await db.logs.update_one({"_id": email}, {"$push": {"logs": {"session": session, "message": message, "app":app, "time":timestamp, "cost":cost}}}, upsert=True)
    return True