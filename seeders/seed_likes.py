from pymongo import MongoClient
import os
from dotenv import load_dotenv
import random

# Load environment variables
load_dotenv()

# Connect to MongoDB
mongo_uri = os.getenv('MONGO_URI')
client = MongoClient(mongo_uri)
db = client['collaborativefilteringtest']
likes_collection = db['likes']
users_collection = db['users']
posts_collection = db['posts']

# Fetch existing user IDs and post IDs from the 'users' and 'posts' collections
user_ids = [str(user['_id']) for user in users_collection.find({}, {'_id': 1})]
post_ids = [str(post['_id']) for post in posts_collection.find({}, {'_id': 1})]

# Check if there are enough user IDs and post IDs
if len(user_ids) < 20 or len(post_ids) < 20:
    raise ValueError("There are not enough user IDs or post IDs in the database.")

# Define like data with custom _id
likes = []
for i in range(20):
    like = {
        "user_id": random.choice(user_ids),
        "post_id": random.choice(post_ids)
    }
    likes.append(like)

# Insert data into the collection
result = likes_collection.insert_many(likes).inserted_ids
print(f"Likes seeded successfully!")
