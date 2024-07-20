from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv
import random

# Load environment variables
load_dotenv()

# Connect to MongoDB
mongo_uri = os.getenv('MONGO_URI')
client = MongoClient(mongo_uri)
db = client['collaborativefilteringtest']
posts_collection = db['posts']
users_collection = db['users']

# Fetch existing user IDs from the 'users' collection and convert them to strings
user_ids = [str(user['_id']) for user in users_collection.find({}, {'_id': 1})]

# Check if there are enough user IDs
if len(user_ids) < 20:
    raise ValueError("There are not enough user IDs in the database.")

# Define post data with custom _id
posts = []
for i in range(20):
    post = {
        "id_user": random.choice(user_ids),
        "title": f"Post Title {i+1}",
        "question": f"What is the best way to learn something new? {i+1}",
        "topic": f"Topic {i+1}",
        "date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "post_pic": ""
    }
    posts.append(post)

# Insert data into the collection
result = posts_collection.insert_many(posts).inserted_ids
print(f"Posts seeded successfully!")
