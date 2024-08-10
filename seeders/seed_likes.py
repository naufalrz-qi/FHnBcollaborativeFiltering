import random
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
mongo_uri = os.getenv('MONGO_URI')
client = MongoClient(mongo_uri)
db = client[os.getenv('MONGO_DB_NAME')]

# Koleksi pengguna dan postingan
users_collection = db['users']
posts_collection = db['posts']
likes_collection = db['likes']

def add_likes_for_users_once():
    users = users_collection.find()
    posts = list(posts_collection.find())
    post_ids = [str(post['_id']) for post in posts]  # Konversi _id postingan menjadi string

    for user in users:
        user_id = str(user['_id'])  # Konversi _id pengguna menjadi string
        num_likes = random.randint(1, 300)
        liked_posts = random.sample(post_ids, num_likes)

        for post_id in liked_posts:
            # Cek apakah like ini sudah ada di koleksi likes
            existing_like = likes_collection.find_one({'user_id': user_id, 'post_id': post_id})
            if not existing_like:
                like = {
                    'user_id': user_id,
                    'post_id': post_id
                }
                likes_collection.insert_one(like)

# Memanggil fungsi
add_likes_for_users_once()
