from database import connect_to_notes_database
import os, json
async def main():
    db = await connect_to_notes_database()
    path = "/home/iiitkota/Documents/Iiitknotes/notes"
    files = os.listdir(path)
    for file in files:
        with open(f"{path}/{file}") as f:
            data = json.loads(f.read())
            g = "iiitkota"
            getattr(db, g).insert_one({"_id":file.split(".")[0], "data":data})
            
    
import asyncio

asyncio.run(main())