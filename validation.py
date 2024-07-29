import os
import re
from pymongo import MongoClient
from bson import ObjectId
import bcrypt
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
# Connect to MongoDB
mongo_uri = os.getenv('MONGO_URI')
client = MongoClient(mongo_uri)
db = client[os.getenv('MONGO_DB_NAME')]
users_collection = db['users']
topics_collection = db['topics']

def validate_phone_number(phone_number):
    """Validate phone number format."""
    return re.match(r'^\+?1?\d{9,15}$', phone_number) is not None

def is_unique(field, value, collection):
    """Check if value is unique in a given field within a specified collection."""
    return collection.count_documents({field: value}) == 0

def allowed_file(filename, allowedExtensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowedExtensions

def ensure_admin_exists():
    """Ensure that there is at least one admin user."""
    admin_user = users_collection.find_one({"role": "admin"})
    if not admin_user:
        # Create a default admin user
        username = "admin"
        password = "admin123"
        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        new_admin = {
            "username": username,
            "password": hashed_pw,
            "profile_name": "Administrator",
            "email": "admin@example.com",
            "role": "admin",
            "status": "verified",
            "gender": "",
            "academic_info": "",
            "workplace": "",
            "service": "",
            "phone_number": "",
            "profile_pic": "",
            "profile_pic_real": "profile_pics/profile_placeholder.png",
            "profile_info": ""
        }

        users_collection.insert_one(new_admin)
        print("Default admin user created. Username: admin, Password: admin123")
