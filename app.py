from flask import Flask, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
import bcrypt
from bson import ObjectId
from dotenv import load_dotenv
import os
import json
from flask_wtf.csrf import CSRFProtect
from datetime import datetime
from alg_collaborativeFiltering import train_model
from validation import validate_phone_number, is_unique, ensure_admin_exists  # Import the validation functions
from controllers.posts.routes import post_create, post_delete, post_like, post_unlike, post_edit, posts_by_topic
from controllers.auth.routes import auth_login, auth_logout, auth_register
from controllers.algorithm.routes import load_recommendations

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
csrf = CSRFProtect(app)
csrf.init_app(app)

# Connect to MongoDB
mongo_uri = os.getenv('MONGO_URI')
client = MongoClient(mongo_uri)
db = client['collaborativefilteringtest']
users_collection = db['users']
posts_collection = db['posts']
topics_collection = db['topics']
likes_collection = db['likes']

app.config['UPLOAD_FOLDER'] = 'static/uploads/post/img'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}


@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('forum'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    return auth_login()

@app.route('/register', methods=['GET', 'POST'])
def register():
    return auth_register()

@app.route('/logout')
def logout():
    return auth_logout()

@app.route('/forum', methods=['GET', 'POST'])
def forum():
    if 'username' not in session:
        return redirect(url_for('index'))

    user_id = session.get('user_id')
    posts = list(posts_collection.find().sort("date", -1))
    topics = list(topics_collection.find())
    
    # Kumpulkan semua likes dari pengguna yang sedang login
    user_likes = set(str(like['post_id']) for like in likes_collection.find({"user_id": user_id}))
    user = users_collection.find_one({'_id':ObjectId(user_id)})
    profilename= user['profile_name']
    # Fetch the number of likes for each post
    for post in posts:
        post['like_count'] = likes_collection.count_documents({"post_id": str(post['_id'])})
        post['_id'] = str(post['_id'])  # Pastikan _id diubah menjadi string

    recommendations = load_recommendations(user_id)  # Load recommendations for current user
    return render_template('forum/forum.html', posts=posts, topics=topics,profilename=profilename, user_likes=user_likes, recommendations=recommendations)

@app.route('/create_post', methods=['GET', 'POST'])
def create_post():
    return post_create(app.config['UPLOAD_FOLDER'], app.config['ALLOWED_EXTENSIONS'])

@app.route('/delete_post/<post_id>', methods=['POST'])
def delete_post(post_id):
    return post_delete(post_id)

@app.route('/edit_post/<post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    return post_edit(post_id,app.config['UPLOAD_FOLDER'], app.config['ALLOWED_EXTENSIONS'])

@app.route('/like_post/<post_id>', methods=['POST'])
def like_post(post_id):
    return post_like(post_id)

@app.route('/unlike_post/<post_id>', methods=['POST'])
def unlike_post(post_id):
    return post_unlike(post_id)

@app.route('/posts/topic/<topic_name>')
def posts_by_topic_route(topic_name):
    return posts_by_topic(topic_name)

if __name__ == '__main__':
    ensure_admin_exists()
    app.run(debug=True)
