from pymongo import MongoClient
from datetime import datetime
import os
from time import sleep

# Mendapatkan URI MongoDB dari environment variable
mongo_uri = os.getenv('MONGO_URI')
client = MongoClient(mongo_uri)
db = client['collaborativefilteringtest']

# Spesifikasi field yang diharapkan untuk setiap koleksi
expected_fields = {
    "users": {
        "username": "",
        "password": "",
        "profile_name": "",
        "email": "",
        "role": "",
        "status": "",
        "gender": "",
        "academic_info": "",
        "workplace": "",
        "service": "",
        "phone_number": "",
        "profile_pic": "",
        "profile_pic_real": "",
        "profile_info": "",
        "date": ""
    },
    "posts": {
        "id_user": "",
        "title": "",
        "question": "",
        "topic": "",
        "date": "",
        "post_pic": ""
    },
    "answers": {
        "post_id": "",
        "user_id": "",
        "content": "",
        "source": "",
        "answer_pic": "",
        "date": ""
    },
    "topics": {
        "name": "",
        "date": ""
    }
}

def add_missing_fields(collection_name, document):
    current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    updated = False

    # Tambahkan field yang hilang dengan nilai default
    for field, default_value in expected_fields[collection_name].items():
        if field not in document:
            if field == "date" and default_value == "":
                document[field] = current_date
            else:
                document[field] = default_value
            updated = True
    
    return document, updated

def check_and_update_collection(collection_name):
    collection = db[collection_name]
    documents = collection.find()

    for document in documents:
        document, updated = add_missing_fields(collection_name, document)
        if updated:
            collection.update_one({"_id": document["_id"]}, {"$set": document})
            print(f"Updated document with id {document['_id']} in collection {collection_name}")

if __name__ == "__main__":
    for collection_name in expected_fields.keys():
        check_and_update_collection(collection_name)
    print("Field check and update completed.")

