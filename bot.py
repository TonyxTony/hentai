from pymongo import MongoClient

# MongoDB connection details
MONGO_URI = "mongodb+srv://Anime:Tony123@animedb.veb4qyk.mongodb.net/?retryWrites=true&w=majority"
DB_NAME = "anime_stream"
COLLECTION_NAME = "stream_db"

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# Old and new usernames
old_username = "@Anime_spectrum_official"
new_username = "@Anime_x_spectrum"

# Update all documents containing the old username in the caption
docs = collection.find({"caption": {"$regex": old_username}})
count = 0

for doc in docs:
    new_caption = doc["caption"].replace(old_username, new_username)
    collection.update_one({"_id": doc["_id"]}, {"$set": {"caption": new_caption}})
    count += 1

print(f"✅ Successfully updated {count} documents.")
