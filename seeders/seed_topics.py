import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Connect to MongoDB
mongo_uri = os.getenv('MONGO_URI')
client = MongoClient(mongo_uri)
db = client['collaborativefilteringtest']
topics_collection = db['topics']

# Define a list of topics to seed
topics = [
    {"name": "Health"},
    {"name": "Beauty"},
    {"name": "Fitness"},
    {"name": "Nutrition"},
    {"name": "Mental Health"},
    {"name": "Skincare"},
    {"name": "Haircare"},
    {"name": "Exercise"},
    {"name": "Diet"},
    {"name": "Wellness"}
]


existing_topics = topics_collection.find()
existing_topic_names = [topic['name'] for topic in existing_topics]

for topic in topics:
    if topic['name'] not in existing_topic_names:
        topics_collection.insert_one(topic)
        print(f"Inserted topic: {topic['name']}")
    else:
        print(f"Topic already exists: {topic['name']}")

