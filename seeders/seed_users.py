from pymongo import MongoClient
from datetime import datetime
import bcrypt
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Connect to MongoDB
mongo_uri = os.getenv('MONGO_URI')
client = MongoClient(mongo_uri)
db = client['collaborativefilteringtest']
users_collection = db['users']

# Define user data with custom _id
users = [
    {
        "username":f"user{i}",
        "password": bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt()),
        "profile_name": "Alice",
        "email": f"user{i}@example.com",
        "role": "normal",
        "status": "verified",
        "gender": "female",
        "phone_number": "1234567890",
        "profile_pic": "",
        "profile_pic_real": "profile_pics/profile_placeholder.png",
        "profile_info": ""
    }
    for i in range(1, 21)
]

# Insert data into the collection
users_collection.insert_many(users).inserted_ids
print("Users seeded successfully!")
