import os
import time
import logging
from pymongo import MongoClient, errors

# Setup logging to both console and file
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("pipeline.log"),
        logging.StreamHandler()
    ]
)

class MongoPipeline:
    def __init__(self, uri="mongodb://localhost:27017/", db_name="PropertyBot", collection_name="listings"):
        self.uri = uri
        self.db_name = db_name
        self.collection_name = collection_name
        self.client = None
        self.db = None
        self.collection = None

    def open(self):
        try:
            self.client = MongoClient(self.uri, serverSelectionTimeoutMS=5000)
            self.client.server_info()
            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]
            self.collection.create_index("url", unique=True)
            logging.info("✅ MongoDB connected and index ensured.")
        except errors.ServerSelectionTimeoutError as e:
            logging.error(f"❌ MongoDB connection failed: {e}")
            raise SystemExit("❌ Cannot connect to MongoDB, exiting.")

    def process_item(self, item, max_retries=3):
        retries = 0
        while retries < max_retries:
            try:
                self.collection.insert_one(item)
                logging.info(f"✅ Inserted: {item.get('url')}")
                return
            except errors.DuplicateKeyError:
                logging.warning(f"⚠️ Duplicate skipped: {item.get('url', '[no url]')}")
                return
            except Exception as e:
                retries += 1
                logging.error(f"❌ Insert failed (attempt {retries}): {e}")
                time.sleep(2)

        logging.error(f"❌ Final failure inserting item after {max_retries} retries: {item.get('url', '[no url]')}")

    def remove_duplicates(self):
        logging.info("🧹 Running duplicate cleanup...")
        pipeline = [
            {"$group": {
                "_id": "$url",
                "ids": {"$addToSet": "$_id"},
                "count": {"$sum": 1}
            }},
            {"$match": {
                "count": {"$gt": 1}
            }}
        ]

        try:
            duplicates = self.collection.aggregate(pipeline)
            removed = 0
            for doc in duplicates:
                ids = doc["ids"]
                ids.pop(0)  # Keep one and delete the rest
                result = self.collection.delete_many({"_id": {"$in": ids}})
                removed += result.deleted_count

            logging.info(f"✅ Removed {removed} duplicate records.")
        except Exception as e:
            logging.error(f"❌ Error during duplicate cleanup: {e}")

    def close(self):
        if self.client:
            self.client.close()
            logging.info("🔒 MongoDB connection closed.")
