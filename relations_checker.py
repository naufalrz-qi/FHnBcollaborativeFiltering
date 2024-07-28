from pymongo import MongoClient
from bson import ObjectId
from bson.errors import InvalidId
import os
from time import sleep

mongo_uri = os.getenv('MONGO_URI')
client = MongoClient(mongo_uri)
db = client['collaborativefilteringtest']

def is_valid_objectid(id):
    try:
        ObjectId(id)
        return True
    except (InvalidId, TypeError):
        return False

def check_and_remove_orphans():
    # Memeriksa posts tanpa user yang valid
    orphaned_posts = db.posts.find({"id_user": {"$exists": True}})
    for post in orphaned_posts:
        if not is_valid_objectid(post["id_user"]) or not db.users.find_one({"_id": ObjectId(post["id_user"])}):
            db.posts.delete_one({"_id": ObjectId(post["_id"])})
            print(f"Deleted orphaned post with id {post['_id']}")

    # Memeriksa answers tanpa user yang valid
    orphaned_answers = db.answers.find({"user_id": {"$exists": True}})
    for answer in orphaned_answers:
        if not is_valid_objectid(answer["user_id"]) or not db.users.find_one({"_id": ObjectId(answer["user_id"])}):
            db.answers.delete_one({"_id": ObjectId(answer["_id"])})
            print(f"Deleted orphaned answer with id {answer['_id']}")

    # Memeriksa answers tanpa post yang valid
    orphaned_answers = db.answers.find({"post_id": {"$exists": True}})
    for answer in orphaned_answers:
        if not is_valid_objectid(answer["post_id"]) or not db.posts.find_one({"_id": ObjectId(answer["post_id"])}):
            db.answers.delete_one({"_id": ObjectId(answer["_id"])})
            print(f"Deleted orphaned answer with id {answer['_id']}")

    # Memeriksa replies tanpa user yang valid
    orphaned_replies = db.replies.find({"user_id": {"$exists": True}})
    for reply in orphaned_replies:
        if not is_valid_objectid(reply["user_id"]) or not db.users.find_one({"_id": ObjectId(reply["user_id"])}):
            db.replies.delete_one({"_id": ObjectId(reply["_id"])})
            print(f"Deleted orphaned reply with id {reply['_id']}")

    # Memeriksa replies tanpa answer yang valid
    orphaned_replies = db.replies.find({"answer_id": {"$exists": True}})
    for reply in orphaned_replies:
        if not is_valid_objectid(reply["answer_id"]) or not db.answers.find_one({"_id": ObjectId(reply["answer_id"])}):
            db.replies.delete_one({"_id": ObjectId(reply["_id"])})
            print(f"Deleted orphaned reply with id {reply['_id']}")

    # Memeriksa likes tanpa user yang valid
    orphaned_likes = db.likes.find({"user_id": {"$exists": True}})
    for like in orphaned_likes:
        if not is_valid_objectid(like["user_id"]) or not db.users.find_one({"_id": ObjectId(like["user_id"])}):
            db.likes.delete_one({"_id": ObjectId(like["_id"])})
            print(f"Deleted orphaned like with id {like['_id']}")

    # Memeriksa likes tanpa post yang valid
    orphaned_likes = db.likes.find({"post_id": {"$exists": True}})
    for like in orphaned_likes:
        if not is_valid_objectid(like["post_id"]) or not db.posts.find_one({"_id": ObjectId(like["post_id"])}):
            db.likes.delete_one({"_id": ObjectId(like["_id"])})
            print(f"Deleted orphaned like with id {like['_id']}")

    print("Integrity check completed.")

if __name__ == "__main__":
    check_and_remove_orphans()
