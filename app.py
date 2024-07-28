from flask import Flask, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
import bcrypt
from bson import ObjectId
from dotenv import load_dotenv
import os
import json
from flask_wtf.csrf import CSRFProtect
from datetime import datetime, timedelta
from alg_collaborativeFiltering import train_model
from alg_collaborativeFilteringSearch import train_search_model, search_posts
from validation import validate_phone_number, is_unique, ensure_admin_exists  # Import the validation functions
from controllers.posts.routes import post_create, post_delete, post_like, post_unlike, post_edit, posts_by_topic, details_post, post_view
from controllers.answers.routes import answer_create, answer_edit, answer_delete
from controllers.auth.routes import auth_login, auth_logout, auth_register, auth_settings, auth_profile
from controllers.algorithm.routes import load_recommendations
import subprocess
import re

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
answers_collection = db['answers']
topics_collection = db['topics']
likes_collection = db['likes']

app.config['UPLOAD_POST'] = 'static/uploads/post/img'
app.config['UPLOAD_ANSWER'] = 'static/uploads/answer/img'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

venv_python = os.path.join(os.getcwd(), 'venv', 'Scripts', 'python.exe') if os.name == 'nt' else os.path.join(os.getcwd(), 'venv', 'bin', 'python')

# Fungsi untuk menjalankan skrip field_checker.py dan relations_checker.py
def run_checkers():
    subprocess.Popen([venv_python, os.path.join(os.getcwd(), "field_checker.py")])
    subprocess.Popen([venv_python, os.path.join(os.getcwd(), "relations_checker.py")])

# Middleware yang dijalankan sebelum setiap permintaan
@app.before_request
def before_request():
    run_checkers()

def is_url(string):
    # Regex pattern to match URLs
    url_pattern = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https:// or ftp://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # ...or ipv4
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # ...or ipv6
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    return re.match(url_pattern, string) is not None

# Register the function with Jinja2 environment
app.jinja_env.globals.update(is_url=is_url)

@app.route('/')
def index():
    # if 'username' in session:
    #     return redirect(url_for('forum'))
    return render_template('index.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'username' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    start_of_today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Query untuk menghitung total topic
    total_topics = topics_collection.count_documents({})
    
    # Query untuk menghitung total post terbaru (misal dalam 24 jam terakhir)
    last_24_hours = datetime.now() - timedelta(days=1)
    total_latest_posts = posts_collection.count_documents({"date": {"$gte": last_24_hours}})
    
    # Query untuk menghitung total topic
    total_users = users_collection.count_documents({})
    
    # Query untuk menghitung total post terbaru (misal dalam 24 jam terakhir)
    last_24_hours = datetime.now() - timedelta(days=1)
    total_latest_posts = posts_collection.count_documents({"date": {"$gte": last_24_hours}})
    
    # Query untuk menghitung total keseluruhan post
    total_posts = posts_collection.count_documents({})
    
    # Query untuk menghitung total likes
    total_likes = likes_collection.count_documents({})
    
    # Query untuk menghitung total likes hari ini
    
    total_likes_today = likes_collection.count_documents({"date": {"$gte": start_of_today}})
    
    # Query untuk menghitung total jawaban
    total_answers = answers_collection.count_documents({})
    
    # Query untuk menghitung total jawaban hari ini
    total_answers_today = answers_collection.count_documents({"date": {"$gte": start_of_today}})
    
    return render_template('admin/dashboard.html', total_topics=total_topics, total_latest_posts=total_latest_posts, 
                           total_posts=total_posts, total_likes=total_likes, total_likes_today=total_likes_today, 
                           total_answers=total_answers, total_answers_today=total_answers_today, total_users=total_users)

@app.route('/login', methods=['GET', 'POST'])
def login():
    return auth_login()

@app.route('/register', methods=['GET', 'POST'])
def register():
    return auth_register()

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    return auth_settings()

@app.route('/logout', methods=['POST'])
def logout():
    return auth_logout()

@app.route('/forum', methods=['GET', 'POST'])
def forum():
    # if 'username' not in session:
    #     return redirect(url_for('index'))
    
    user_id = session.get('user_id')
    recommendations = load_recommendations(user_id)  # Load recommendations for current user
    recommendation_ids = [ObjectId(rec["_id"]) for rec in recommendations]
    posts = list(posts_collection.find({"_id": {"$nin": recommendation_ids}}).sort("date", -1))
    topics = list(topics_collection.find())
    
    # Kumpulkan semua likes dari pengguna yang sedang login
    user_likes = set(str(like['post_id']) for like in likes_collection.find({"user_id": user_id}))

    # Fetch the number of likes for each post
    for post in posts:
        user = users_collection.find_one({'_id': ObjectId(post['id_user'])})
        post['answer_count'] = answers_collection.count_documents({"post_id": str(post['_id'])})
        post['like_count'] = likes_collection.count_documents({"post_id": str(post['_id'])})
        post['_id'] = str(post['_id'])  # Pastikan _id diubah menjadi string
        post['author'] = user['username']
        post['author_role'] = user['role']
        post['author_status'] = user['status']
    
    for post in recommendations:
        user = users_collection.find_one({'_id': ObjectId(post['id_user'])})
        post['answer_count'] = answers_collection.count_documents({"post_id": str(post['_id'])})
        post['like_count'] = likes_collection.count_documents({"post_id": str(post['_id'])})
        post['_id'] = str(post['_id'])  # Pastikan _id diubah menjadi string
        post['author'] = user['username']
        post['author_role'] = user['role']
        post['author_status'] = user['status']
        
    return render_template('forum/forum.html', posts=posts, topics=topics, user_likes=user_likes, recommendations=recommendations)

@app.route('/create_post', methods=['GET', 'POST'])
def create_post():
    return post_create(app.config['UPLOAD_POST'], app.config['ALLOWED_EXTENSIONS'])

@app.route('/delete_post/<post_id>', methods=['POST'])
def delete_post(post_id):
    return post_delete(post_id,app.config['UPLOAD_POST']  )

@app.route('/edit_post/<post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    return post_edit(post_id,app.config['UPLOAD_POST'], app.config['ALLOWED_EXTENSIONS'])

@app.route('/like_post/<post_id>', methods=['POST'])
def like_post(post_id):
    return post_like(post_id)

@app.route('/unlike_post/<post_id>', methods=['POST'])
def unlike_post(post_id):
    return post_unlike(post_id)

@app.route('/posts/topic/<topic_name>')
def posts_by_topic_route(topic_name):
    return posts_by_topic(topic_name)

@app.route('/post/<post_id>')
def post_detail(post_id):
    return details_post(post_id)


@app.route('/topics')
def topics():
    topics = list(topics_collection.find())
    return render_template('forum/topics.html', topics=topics)

@app.route('/answer_post/<post_id>', methods=['POST'])
def answer_post(post_id):
    return answer_create(post_id,app.config['UPLOAD_ANSWER'], app.config['ALLOWED_EXTENSIONS'] )

@app.route('/edit_answer/<answer_id>', methods=['GET', 'POST'])
def edit_answer(answer_id):
    return answer_edit(answer_id,app.config['UPLOAD_ANSWER'], app.config['ALLOWED_EXTENSIONS'] )

@app.route('/delete_answer/<answer_id>', methods=['POST'])
def delete_answer(answer_id):
    return answer_delete(answer_id, app.config['UPLOAD_ANSWER'])


@app.route('/search', methods=['GET'])
def search():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    query = request.args.get('query')
    user_id = request.args.get('user_id')
    
    # Construct search query
    search_query = {
        "$or": [
            { "date": { "$regex": query, "$options": "i" } },
            { "question": { "$regex": query, "$options": "i" } },
            { "topic": { "$regex": query, "$options": "i" } },
            { "id_user": { "$regex": query, "$options": "i" } },
            { "title": { "$regex": query, "$options": "i" } },
            { "post_pic": { "$regex": query, "$options": "i" } }
        ]
    }
    
    results = list(posts_collection.find(search_query))
    
    recommendations = []
    topics = list(topics_collection.find())
    if query:
        train_search_model(query)
        recommendations = search_posts(query, user_id)
    
    # Filter out recommended posts from results
    recommended_post_ids = [ObjectId(post['_id']) for post in recommendations]
    filtered_results = [post for post in results if ObjectId(post['_id']) not in recommended_post_ids]
    
    user_likes = set(str(like['post_id']) for like in likes_collection.find({"user_id": user_id}))
    
    for post in filtered_results:
        user = users_collection.find_one({'_id': ObjectId(post['id_user'])})
        post['answer_count'] = answers_collection.count_documents({"post_id": str(post['_id'])})
        post['like_count'] = likes_collection.count_documents({"post_id": str(post['_id'])})
        post['_id'] = str(post['_id'])  # Pastikan _id diubah menjadi string
        post['author'] = user['username']
        post['author_role'] = user['role']
        post['author_status'] = user['status']
    
    for post in recommendations:
        user = users_collection.find_one({'_id': ObjectId(post['id_user'])})
        post['answer_count'] = answers_collection.count_documents({"post_id": str(post['_id'])})
        post['like_count'] = likes_collection.count_documents({"post_id": str(post['_id'])})
        post['_id'] = str(post['_id'])  # Pastikan _id diubah menjadi string
        post['author'] = user['username']
        post['author_role'] = user['role']
        post['author_status'] = user['status']
    
    return render_template('forum/search.html', results=filtered_results, topics=topics, user_likes=user_likes, recommendations=recommendations)

@app.route('/profile/<user_id>')
def profile(user_id):
    return auth_profile(user_id)

# Topics di admin
    
@app.route('/admin/posts')
def view_posts():
    return post_view()

@app.route('/admin/topics')
def view_topics():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    topics = list(topics_collection.find().sort("date", -1))
    return render_template('admin/features/topics.html', topics=topics)

@app.route('/admin/topics/create', methods=['POST'])
def create_topic():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    new_topic_name = request.form['new_topic_name']
    if not is_unique('name', new_topic_name, topics_collection):
        flash('Topic already exists')
    else:
        topics_collection.insert_one({'name': new_topic_name})
        flash('Topic created successfully!')
    
    return redirect(url_for('view_topics'))

@app.route('/admin/topics/edit/<topic_id>', methods=['POST'])
def edit_topic(topic_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    new_name = request.form['new_name']
    if not is_unique('name', new_name, topics_collection):
        flash('Topic name already exists')
    else:
        topics_collection.update_one({'_id': ObjectId(topic_id)}, {'$set': {'name': new_name}})
        flash('Topic updated successfully!')
    
    return redirect(url_for('view_topics'))

@app.route('/admin/topics/delete/<topic_id>', methods=['POST'])
def delete_topic(topic_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    topics_collection.delete_one({'_id': ObjectId(topic_id)})
    flash('Topic deleted successfully!')
    
    return redirect(url_for('view_topics'))

# Users di admin
# Check if username is unique
def is_unique_username(username):
    return users_collection.find_one({'username': username}) is None

# Route to view users
# Check if username is unique
def is_unique_username(username):
    return users_collection.find_one({'username': username}) is None

# Route to view users
@app.route('/admin/users')
def view_users():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    users = list(users_collection.find())
    return render_template('admin/features/users.html', users=users)

# Route to create a new user
@app.route('/admin/users/create', methods=['POST'])
def create_user():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = request.form['username']
    password = request.form['password']
    email = request.form['email']
    role = request.form['role']
    status = request.form['status']
    
    if not is_unique_username(username):
        flash('Username already exists')
    else:
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        users_collection.insert_one({
            'username': username,
            'password': hashed_password,
            'email': email,
            'role': role,
            'status': status,
            'date': datetime.now()
        })
        flash('User created successfully!')
    
    return redirect(url_for('view_users'))

# Route to change user role
@app.route('/admin/users/change_role/<user_id>', methods=['POST'])
def change_user_role(user_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    new_role = request.form['role']
    users_collection.update_one({'_id': ObjectId(user_id)}, {'$set': {'role': new_role}})
    flash('User role updated successfully!')
    
    return redirect(url_for('view_users'))

# Route to change user status
@app.route('/admin/users/change_status/<user_id>', methods=['POST'])
def change_user_status(user_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    new_status = request.form['status']
    users_collection.update_one({'_id': ObjectId(user_id)}, {'$set': {'status': new_status}})
    flash('User status updated successfully!')
    
    return redirect(url_for('view_users'))

# Route to delete a user
@app.route('/admin/users/delete/<user_id>', methods=['POST'])
def delete_user(user_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    users_collection.delete_one({'_id': ObjectId(user_id)})
    flash('User deleted successfully!')
    
    return redirect(url_for('view_users'))

@app.route('/admin/answers')
def view_answers():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    answers = list(answers_collection.find())
    for answer in answers:
        post = posts_collection.find_one({"_id": ObjectId(answer['post_id'])})
        user = users_collection.find_one({"_id": ObjectId(answer['user_id'])})
        answer['post_title'] = post['title'] if post else "Unknown"
        answer['author'] = user['username'] if user else "Unknown"
    return render_template('admin/features/answers.html', answers=answers)


if __name__ == '__main__':
    ensure_admin_exists()
    app.run(debug=True)
