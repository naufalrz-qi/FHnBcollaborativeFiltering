from pymongo import MongoClient
import datetime
import os
from dotenv import load_dotenv

load_dotenv()
mongo_uri = os.getenv('MONGO_URI')
client = MongoClient(mongo_uri)
db = client[os.getenv('MONGO_DB_NAME')]
users_collection = db["users"]

# Pipeline agregasi untuk menambahkan field baru
pipeline = [
    {
        "$set": {
            "gender": {
                "$ifNull": ["$gender", ""]
            },
            "academic_info": {
                "$ifNull": ["$academic_info", ""]
            },
            "workplace": {
                "$ifNull": ["$workplace", ""]
            },
            "service": {
                "$ifNull": ["$service", ""]
            },
            "phone_number": {
                "$ifNull": ["$phone_number", ""]
            },
            "profile_pic": {
                "$ifNull": ["$profile_pic", ""]
            },
            "profile_pic_real": {
                "$ifNull": ["$profile_pic_real", "profile_pics/profile_placeholder.png"]
            },
            "profile_info": {
                "$ifNull": ["$profile_info", ""]
            },
            "date": {
                "$ifNull": ["$date", datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
            }
        }
    },
    {
        "$out": "users"  # Menulis hasil kembali ke koleksi users
    }
]

# Jalankan pipeline agregasi
users_collection.aggregate(pipeline)

print("Fields updated successfully!")
