import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
import json
from bson import json_util, ObjectId
import uuid
from storage import driveauth
from googleapiclient.http import MediaFileUpload
import asyncio
import asyncio
import logging
from logging.handlers import QueueHandler, QueueListener
import queue


MONGODB_URL = "mongodb+srv://***:***@***.cbvk0so.mongodb.net/?retryWrites=true&w=majority&appName=devh"
# RESTORE_MONGODB_URL = "mongodb+srv://mongodb:***@mongodbdevh.9fqlqam.mongodb.net/?retryWrites=true&w=majority&appName=mongodbdevh"
BACKUP_DIR = "mongodb_backup"


# Create a queue for log messages
log_queue = queue.Queue()

# Configure the root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# Create a queue handler and add it to the root logger
queue_handler = QueueHandler(log_queue)
root_logger.addHandler(queue_handler)

# Create a file handler
file_handler = logging.FileHandler('database_backup_log.txt')
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)

# Create a console handler
# console_handler = logging.StreamHandler()
# console_handler.setLevel(logging.INFO)
# console_formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
# console_handler.setFormatter(console_formatter)

# Create a queue listener and start it
listener = QueueListener(log_queue, file_handler)
listener.start()

async def alog(msg, level=logging.INFO, logger=None):
    if logger is None:
        logger = logging.getLogger()
    
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, logger.log, level, msg)



async def aprint(*args, **kwargs):
    loop = asyncio.get_running_loop()
    kwargs['flush'] = True  # Ensure output is flushed immediately
    await loop.run_in_executor(None, lambda: print(*args, **kwargs))
    # Log the message
    del kwargs['flush']
    if 'end' in kwargs:
        
        del kwargs['end']

    await alog(*args, **kwargs)

    


async def backup_document(db, database_name, collection_name, document):
    doc_id = str(document.get('_id', uuid.uuid4()))
    file_name = f"{doc_id}.json"
    dir_path = os.path.join(BACKUP_DIR, database_name, collection_name)
    os.makedirs(dir_path, exist_ok=True)
    file_path = os.path.join(dir_path, file_name)
    
    with open(file_path, 'w') as f:
        await aprint(" .", end="")
        json.dump(json.loads(json_util.dumps(document)), f, indent=2)

async def backup_collection(db, database_name, collection_name):
    await aprint(f"Backing up: {database_name}/{collection_name} ", end="")
    collection = db[collection_name]
    v = None
    try:
        async for document in collection.find():
            await backup_document(db, database_name, collection_name, document)
    except Exception as e:
        await aprint(f" -> Error: {str(e)}")
    finally:
        v = 1
    while True:
        if v:
            break
        
    await aprint(f" -> Done.")

async def backup_database(client, database_name):
    db = client[database_name]
    collection_names = await db.list_collection_names()
    for collection_name in collection_names:
        await backup_collection(db, database_name, collection_name)

async def backup_all_databases():
    client = AsyncIOMotorClient(MONGODB_URL)
    database_names = await client.list_database_names()
    for database_name in database_names:
        if database_name not in ['admin', 'local', 'config', "WorldDB", "LinkToFileUploaderBot", "MY_UPLOADER"]:  # Skip some databases
            await backup_database(client, database_name)
    await aprint("All databases backed up.")

async def start_backup():
    await backup_all_databases()
    from datetime import datetime
    current_date_and_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    os.system(f"tar -czf {BACKUP_DIR}_{current_date_and_time}.tar.gz {BACKUP_DIR}")
    import shutil
    shutil.rmtree(BACKUP_DIR)

    drive_service = driveauth.authenticate()
    folder_id = "1mwNqxosVh6JCDSoc5s7Wv93A30WspfMN"
    file_metadata = {
        'name': f"{BACKUP_DIR}_{current_date_and_time}.tar.gz",
        'parents': [folder_id]
    }
    media = MediaFileUpload(f"{BACKUP_DIR}_{current_date_and_time}.tar.gz", mimetype='application/gzip', resumable=True)
    file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    await aprint("Backup uploaded to Google Drive.")
    await aprint(f"Backup uploaded to Google Drive with ID: {file.get('id')}")    
    os.remove(f"{BACKUP_DIR}_{current_date_and_time}.tar.gz")

    
if __name__ == "__main__":
    asyncio.run(start_backup())


# async def restore_document(db, database_name, collection_name, file_path):
#     with open(file_path, 'r') as f:
#         document = json.load(f)
#     bson_document = json_util.loads(json.dumps(document))
#     collection = db[collection_name]
#     await collection.replace_one({'_id': bson_document['_id']}, bson_document, upsert=True)

# async def restore_collection(db, database_name, collection_name):
#     dir_path = os.path.join(BACKUP_DIR, database_name, collection_name)
#     if not os.path.exists(dir_path):
#         await aprint(f"No backup found for collection: {collection_name}")
#         return
#     for file_name in os.listdir(dir_path):
#         if file_name.endswith('.json'):
#             file_path = os.path.join(dir_path, file_name)
#             await restore_document(db, database_name, collection_name, file_path)
#     await aprint(f"Restored collection: {collection_name}")

# async def restore_database(client, database_name):
#     db = client[database_name]
#     database_dir = os.path.join(BACKUP_DIR, database_name)
#     if not os.path.exists(database_dir):
#         await aprint(f"No backup found for database: {database_name}")
#         return
#     for collection_name in os.listdir(database_dir):
#         await restore_collection(db, database_name, collection_name)
#     await aprint(f"Restored database: {database_name}")

# async def restore_all_databases():
#     client = AsyncIOMotorClient(MONGODB_URL)
#     for database_name in os.listdir(BACKUP_DIR):
#         await restore_database(client, database_name)
#     await aprint("All databases restored.")


# await backup_all_databases()

