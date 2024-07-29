from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

mongo_uri = os.getenv('MONGO_URI')
client = MongoClient(mongo_uri)
db = client[os.getenv('MONGO_DB_NAME')]
users_collection = db['users']
posts_collection = db['posts']
topics_collection = db['topics']
likes_collection = db['likes']
answers_collection = db['answers']

from . import routes
