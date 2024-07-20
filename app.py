from flask import Flask, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
import bcrypt
from bson import ObjectId
from dotenv import load_dotenv
import os
import json
from datetime import datetime
from alg_collaborativeFiltering import train_model
from validation import validate_phone_number, is_unique, ensure_admin_exists  # Import the validation functions

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# Connect to MongoDB
mongo_uri = os.getenv('MONGO_URI')
client = MongoClient(mongo_uri)
db = client['collaborativefilteringtest']
users_collection = db['users']
posts_collection = db['posts']
topics_collection = db['topics']
likes_collection = db['likes']

def load_recommendations(user_id):
    with open('recommendations.json', 'r') as file:
        recommendations_data = json.load(file)
    # Ambil rekomendasi untuk user saat ini
    recommended_post_ids = recommendations_data.get(str(user_id), [])
    # Ambil informasi postingan dari database
    recommended_posts = []
    for post_id in recommended_post_ids:
        post = posts_collection.find_one({"_id": ObjectId(post_id)})
        if post:
            post['like_count'] = likes_collection.count_documents({"post_id": post_id})
            recommended_posts.append(post)
    return recommended_posts

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('forum'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].lower()  # Convert to lowercase
        password = request.form['password']
        user = users_collection.find_one({"username": username})

        if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
            session['username'] = username
            session['user_id'] = str(user['_id'])  # Store user ID in session
            return redirect(url_for('forum'))
        else:
            flash('Invalid username/password combination')

    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].lower()  # Convert to lowercase
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        email = request.form['email']
        phone_number = request.form['phone_number']
        profile_name = request.form['profile_name']
        gender = request.form['gender']

        # Validate uniqueness
        if not is_unique('username', username, users_collection):
            flash('Username is already taken')
        elif not is_unique('email', email, users_collection):
            flash('Email is already registered')
        elif not is_unique('phone_number', phone_number, users_collection):
            flash('Phone number is already registered')
        elif not validate_phone_number(phone_number):
            flash('Invalid phone number format')
        elif password != confirm_password:
            flash('Passwords do not match')
        else:
            hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            new_user = {
                "username": username,
                "password": hashed_pw,
                "profile_name": profile_name,
                "email": email,
                "role": "normal",
                "status": "unverified",
                "gender": gender,
                "academic_info": "",
                "workplace": "",
                "service": "",
                "phone_number": phone_number,
                "profile_pic": "",
                "profile_pic_real": "profile_pics/profile_placeholder.png",
                "profile_info": ""
            }

            users_collection.insert_one(new_user)
            flash('Registration successful! Please log in.')
            return redirect(url_for('login'))

    return render_template('auth/register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('user_id', None)
    return redirect(url_for('index'))

@app.route('/forum', methods=['GET', 'POST'])
def forum():
    if 'username' not in session:
        return redirect(url_for('index'))

    user_id = session.get('user_id')
    posts = list(posts_collection.find())
    topics = list(topics_collection.find())
    user_likes = set(like['post_id'] for like in likes_collection.find({"user_id": user_id}))

    # Fetch the number of likes for each post
    for post in posts:
        post['like_count'] = likes_collection.count_documents({"post_id": str(post['_id'])})

    recommendations = load_recommendations(user_id)  # Load recommendations for current user
    return render_template('forum/forum.html', posts=posts, topics=topics, user_likes=user_likes, recommendations=recommendations)

@app.route('/create_post', methods=['GET', 'POST'])
def create_post():
    if 'username' not in session:
        return redirect(url_for('index'))
    
    topics = list(topics_collection.find())
    
    if request.method == 'POST':
        title = request.form['title']
        question = request.form['question']
        topic = request.form['topic']
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        post_pic = request.form.get('post_pic', '')

        if topic == 'new_topic':
            new_topic = request.form['new_topic']
            if not is_unique('name', new_topic, topics_collection):
                flash('Topic already exists')
                return render_template('posts/create_post.html', topics=topics)
            else:
                topics_collection.insert_one({'name': new_topic})
                topic = new_topic
        
        posts_collection.insert_one({
            "id_user": session.get('user_id'),
            "title": title,
            "question": question,
            "topic": topic,
            "date": date,
            "post_pic": post_pic
        })

        train_model()  # Update recommendations
        flash('Post created successfully!')
        return redirect(url_for('forum'))

    return render_template('posts/create_post.html', topics=topics)

@app.route('/delete_post/<post_id>')
def delete_post(post_id):
    if 'username' not in session:
        return redirect(url_for('index'))

    posts_collection.delete_one({"_id": ObjectId(post_id)})
    train_model()  # Update recommendations
    flash('Post deleted successfully!')
    return redirect(url_for('forum'))

@app.route('/like_post/<post_id>', methods=['POST'])
def like_post(post_id):
    if 'username' not in session:
        return redirect(url_for('index'))

    user_id = session.get('user_id')
    if not likes_collection.find_one({"user_id": user_id, "post_id": post_id}):
        likes_collection.insert_one({"user_id": user_id, "post_id": post_id})
        train_model()  # Update recommendations
        flash('Post liked!')
    else:
        flash('You already liked this post.')

    return redirect(url_for('forum'))

@app.route('/unlike_post/<post_id>', methods=['POST'])
def unlike_post(post_id):
    if 'username' not in session:
        return redirect(url_for('index'))

    user_id = session.get('user_id')
    like = likes_collection.find_one({"user_id": user_id, "post_id": post_id})
    if like:
        likes_collection.delete_one({"_id": like['_id']})
        train_model()  # Update recommendations
        flash('Post unliked!')
    else:
        flash('You haven\'t liked this post yet.')

    return redirect(url_for('forum'))

if __name__ == '__main__':
    ensure_admin_exists()
    app.run(debug=True)
