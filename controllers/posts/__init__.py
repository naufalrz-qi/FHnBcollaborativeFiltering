from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

# Connect to MongoDB
mongo_uri = os.getenv('MONGO_URI')
client = MongoClient(mongo_uri)
db = client['collaborativefilteringtest']
users_collection = db['users']
posts_collection = db['posts']
topics_collection = db['topics']
likes_collection = db['likes']

from . import routes
