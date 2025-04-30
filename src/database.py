# database.py
from pymongo import MongoClient, DESCENDING, ASCENDING
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
MONGO_URI = os.getenv("MONGODB_URI")
DB_NAME = "Pepe_bot"  # Your target database name

def get_database():
    """Establishes a connection to MongoDB with error handling"""
    try:
        client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=30000,
            socketTimeoutMS=30000
        )
        # Verify connection works
        client.admin.command('ping')
        db = client[DB_NAME]
        return db
    except Exception as e:
        print(f"Database connection failed: {str(e)}")
        return None

def initialize_database():
    """Initializes collections and indexes if they don't exist"""
    db = get_database()
    if db is None:
        return False

    collections_config = {
        "users": [
            {"keys": [("user_id", ASCENDING)], "options": {"unique": True}},
            {"keys": [("username", ASCENDING)]}
        ],
        "command_usage": [
            {"keys": [("user_id", ASCENDING), ("command_name", ASCENDING)], "options": {"unique": True}},
            {"keys": [("command_name", ASCENDING)]}
        ],
        "user_moods": [
            {"keys": [("user_id", ASCENDING)]},
            {"keys": [("detected_at", DESCENDING)]}
        ]
    }

    try:
        existing_collections = db.list_collection_names()

        for collection_name, indexes in collections_config.items():
            if collection_name not in existing_collections:
                db[collection_name].insert_one({"__init__": True})
                db[collection_name].delete_one({"__init__": True})
                print(f"Created collection: {collection_name}")

            current_indexes = db[collection_name].index_information()
            for index in indexes:
                index_name = "_".join([f"{k}_{v}" for k, v in index["keys"]])
                if index_name not in current_indexes:
                    db[collection_name].create_index(
                        index["keys"],
                        **index.get("options", {})
                    )
                    print(f"Created index {index_name} on {collection_name}")

        return True
    except Exception as e:
        print(f"Initialization error: {str(e)}")
        return False

def add_user(user_id: int, username: str):
    db = get_database()
    if db is not None:
        try:
            db.users.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "username": username,
                        "last_seen": datetime.now()
                    },
                    "$setOnInsert": {
                        "join_date": datetime.now(),
                        "message_count": 0,
                        "last_mood": None
                    }
                },
                upsert=True
            )
            return True
        except Exception as e:
            print(f"Error adding user: {str(e)}")
    else:
        print("Failed to connect to the database.")
    return False

def log_command_usage(user_id: int, command_name: str):
    db = get_database()
    if db is not None:
        try:
            db.users.update_one(
                {"user_id": user_id},
                {
                    "$inc": {"message_count": 1},
                    "$set": {"last_seen": datetime.now()}
                }
            )

            db.command_usage.update_one(
                {"user_id": user_id, "command_name": command_name},
                {
                    "$inc": {"usage_count": 1},
                    "$set": {"last_used": datetime.now()}
                },
                upsert=True
            )
            return True
        except Exception as e:
            print(f"Error logging command: {str(e)}")
    return False

def log_user_mood(user_id: int, mood: str):
    db = get_database()
    if db is not None:
        try:
            db.users.update_one(
                {"user_id": user_id},
                {"$set": {"last_mood": mood}}
            )

            db.user_moods.insert_one({
                "user_id": user_id,
                "mood": mood,
                "detected_at": datetime.now()
            })
            return True
        except Exception as e:
            print(f"Error logging mood: {str(e)}")
    return False

def get_user_stats(user_id: int) -> dict:
    db = get_database()
    if db is None:
        return None

    try:
        user = db.users.find_one(
            {"user_id": user_id},
            {"_id": 0, "username": 1, "message_count": 1,
             "last_mood": 1, "join_date": 1, "last_seen": 1}
        )
        if not user:
            return None

        top_commands = list(db.command_usage.find(
            {"user_id": user_id},
            {"_id": 0, "command_name": 1, "usage_count": 1, "last_used": 1}
        ).sort("usage_count", DESCENDING).limit(5))

        mood_history = list(db.user_moods.find(
            {"user_id": user_id},
            {"_id": 0, "mood": 1, "detected_at": 1}
        ).sort("detected_at", DESCENDING).limit(5))

        return {
            **user,
            "top_commands": top_commands,
            "mood_history": mood_history
        }
    except Exception as e:
        print(f"Error getting user stats: {str(e)}")
        return None

def get_server_stats() -> dict:
    db = get_database()
    if db is None:
        return None

    try:
        user_stats = db.users.aggregate([
            {
                "$group": {
                    "_id": None,
                    "total_users": {"$sum": 1},
                    "total_messages": {"$sum": "$message_count"}
                }
            }
        ]).next()

        most_active = db.users.find_one(
            {},
            {"_id": 0, "user_id": 1, "username": 1, "message_count": 1},
            sort=[("message_count", DESCENDING)]
        )

        popular_commands = list(db.command_usage.aggregate([
            {"$group": {
                "_id": "$command_name",
                "total_usage": {"$sum": "$usage_count"}
            }},
            {"$sort": {"total_usage": DESCENDING}},
            {"$limit": 5}
        ]))

        return {
            "total_users": user_stats["total_users"],
            "total_messages": user_stats["total_messages"],
            "most_active_user": most_active,
            "popular_commands": popular_commands
        }
    except Exception as e:
        print(f"Error getting server stats: {str(e)}")
        return None

def cleanup_database(days_old: int = 30):
    db = get_database()
    if db is not None:
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)

            result_moods = db.user_moods.delete_many({
                "detected_at": {"$lt": cutoff_date}
            })

            result_commands = db.command_usage.delete_many({
                "last_used": {"$lt": cutoff_date}
            })

            print(f"Cleaned up: {result_moods.deleted_count} mood records, {result_commands.deleted_count} command logs")
            return True
        except Exception as e:
            print(f"Cleanup error: {str(e)}")
    return False

def get_user_mood(user_id: int):
    db = get_database()
    if db is not None:
        user = db.users.find_one({"user_id": user_id}, {"last_mood": 1})
        return user.get("last_mood") if user else None
    return None

def reset_user_mood(user_id: int):
    db = get_database()
    if db is not None:
        try:
            db.users.update_one(
                {"user_id": user_id},
                {"$unset": {"last_mood": ""}}
            )
            return True
        except Exception as e:
            print(f"Error resetting mood: {str(e)}")
    return False