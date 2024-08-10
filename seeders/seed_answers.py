import random
from datetime import datetime
from bson.objectid import ObjectId
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
answers_collection = db['answers']
topics_collection = db['topics']
likes_collection = db['likes']

users = list(users_collection.find())
topics = list(topics_collection.find({}, {"name": 1, "_id": 0}))
posts = list(posts_collection.find())

def generate_answers(posts, topics, users):
    answers = []
    for user in users:
        num_posts = random.randint(1, 250)
        chosen_posts = random.sample(posts, num_posts)
        for post in chosen_posts:
            topic_name = post['topic']
            answer_content = f"Ini adalah jawaban untuk topic {topic_name} {random.randint(1, 100)}"
            answer = {
                "_id": ObjectId(),
                "post_id": str(post["_id"]),
                "user_id": str(user["_id"]),
                "content": answer_content,
                "source":['http://127.0.0.1'],
                "answer_pic": '',
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            answers.append(answer)
    return answers

# Generate answers
generated_answers = generate_answers(posts, topics, users)

# Insert answers into the collection
result = answers_collection.insert_many(generated_answers)

# Print the result
print(f"Inserted {len(result.inserted_ids)} documents into 'answers' collection.")
