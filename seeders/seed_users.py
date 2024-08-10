from pymongo import MongoClient
from bson import ObjectId, Binary
from faker import Faker
import base64
import datetime

# Inisialisasi Faker
fake = Faker()

# Koneksi ke MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['collaborativefilteringtest2']  # Ganti dengan nama database Anda
collection = db['users']  # Ganti dengan nama koleksi Anda

def generate_random_user():
    return {
        "_id": ObjectId(),
        "username": fake.user_name(),
        "password": Binary(base64.b64decode("JDJiJDEyJDBjcE1NcDhkWmhBLnBkWW80Q09KOHVKdHJaQ1NkLnUwZjNoVzBLSE9jZnJHc2xpNmh6UFRT")),  # Gantilah ini dengan metode enkripsi password yang sesuai
        "profile_name": fake.first_name(),
        "email": fake.email(),
        "role": fake.random_element(elements=("expert", "normal")),  # Ganti dengan role yang relevan
        "status": fake.random_element(elements=("verified", "unverified")),
        "gender": fake.random_element(elements=("male", "female")),
        "phone_number": fake.phone_number(),
        "profile_pic": "",
        "profile_pic_real": "profile_pics/profile_placeholder.png",
        "profile_info": fake.text(max_nb_chars=200),
        "academic_info": fake.text(max_nb_chars=200),
        "workplace": fake.company(),
        "service": fake.job(),
        "date": fake.date_time_this_year()
    }

# Generate and insert random users
for _ in range(200):  # Ganti jumlah ini sesuai kebutuhan
    user_data = generate_random_user()
    collection.insert_one(user_data)

print("Data pengguna acak berhasil dimasukkan ke dalam database.")
