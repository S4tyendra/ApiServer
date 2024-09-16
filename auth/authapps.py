from database import connect_to_database


async def getApp(app_id):
    db = await connect_to_database()
    app = await db.apps.find_one({"app_url": app_id})
    return app


async def getApp_by_id(app_id):
    db = await connect_to_database()
    app = await db.apps.find_one({"_id": app_id})
    return app
