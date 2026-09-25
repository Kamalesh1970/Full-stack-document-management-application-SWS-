from datetime import datetime, timezone

from bson import ObjectId
from pymongo import DESCENDING, MongoClient
from pymongo.errors import PyMongoError

from app.config import settings

client = MongoClient(settings.MONGODB_URI, serverSelectionTimeoutMS=5000)
collection = client[settings.MONGODB_DB]["documents"]

# content holds the extracted text used for search, it never goes back to the client
PUBLIC_FIELDS = {"content": 0, "storedName": 0}


def init_db():
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    # fail fast with a clear message if mongo isn't reachable
    try:
        client.admin.command("ping")
    except PyMongoError as err:
        raise RuntimeError(f"Could not connect to MongoDB, check MONGODB_URI ({err.__class__.__name__})") from None
    collection.create_index([("createdAt", DESCENDING)])


def is_valid_id(doc_id):
    return ObjectId.is_valid(doc_id) and len(doc_id) == 24


def to_public(doc):
    return {
        "_id": str(doc["_id"]),
        "originalName": doc["originalName"],
        "extension": doc["extension"],
        "mimeType": doc["mimeType"],
        "size": doc["size"],
        "createdAt": doc["createdAt"].replace(tzinfo=timezone.utc).isoformat(),
    }


def insert_document(original_name, stored_name, extension, mime_type, size, content):
    doc = {
        "originalName": original_name,
        "storedName": stored_name,
        "extension": extension,
        "mimeType": mime_type,
        "size": size,
        "content": content,
        "createdAt": datetime.now(timezone.utc),
    }
    result = collection.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


def list_documents():
    return list(collection.find({}, PUBLIC_FIELDS).sort([("createdAt", DESCENDING), ("_id", DESCENDING)]))


def list_with_content():
    return list(collection.find({}, {"originalName": 1, "content": 1}))


def get_document(doc_id):
    return collection.find_one({"_id": ObjectId(doc_id)})


def delete_document(doc_id):
    collection.delete_one({"_id": ObjectId(doc_id)})
