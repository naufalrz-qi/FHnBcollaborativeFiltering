from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
def create_topics_collection():

    mongo_uri = os.getenv('MONGO_URI')
    client = MongoClient(mongo_uri)
    db = client[os.getenv('MONGO_DB_NAME')]
    posts_collection = db['posts']
    topics_collection = db['topics']

    # Ambil semua topik dari koleksi posts
    posts = posts_collection.find({}, {'topic': 1})

    # Gunakan set untuk menyimpan topik unik
    unique_topics = set()

    for post in posts:
        topic = post.get('topic')
        if topic:
            unique_topics.add(topic)

    # Masukkan topik unik ke dalam koleksi topics
    topics_collection.delete_many({})  # Bersihkan koleksi sebelumnya jika ada
    topics_documents = [{'name': topic} for topic in unique_topics]
    if topics_documents:
        topics_collection.insert_many(topics_documents)
    
    print(f"Successfully inserted {len(topics_documents)} unique topics into the 'topics' collection.")

# Jalankan fungsi
create_topics_collection()
