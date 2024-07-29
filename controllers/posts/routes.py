from flask import render_template,jsonify, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from . import users_collection, topics_collection, posts_collection, likes_collection, answers_collection
import os
from bson import ObjectId
from datetime import datetime
from alg_collaborativeFilteringwithEvaluation import train_model
from validation import validate_phone_number, is_unique, ensure_admin_exists, allowed_file
from controllers.algorithm.routes import load_recommendations_by_topic
import json


def details_post(post_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    answers = list(answers_collection.find({"post_id": post_id}).sort("date", -1))
    post = posts_collection.find_one({"_id": ObjectId(post_id)})
    if not post:
        flash("Post not found", "danger")
        return redirect(url_for('forum'))
    
    post['answer_count'] = answers_collection.count_documents({"post_id": post_id})
    post['like_count'] = likes_collection.count_documents({"post_id": post_id})
    post['_id'] = str(post['_id'])  # Ensure _id is a string
    user_likes = set(str(like['post_id']) for like in likes_collection.find({"user_id": session.get('user_id')}))
    user = users_collection.find_one({'_id': ObjectId(post['id_user'])})
    post['author'] = user['username']
    post['author_role'] = user['role']
    post['author_status'] = user['status']
    
    for answer in answers:
        answerer = users_collection.find_one({'_id': ObjectId(answer['user_id'])})
        answer['author'] = answerer['username']
        answer['author_role'] = answerer['role']
        answer['author_status'] = answerer['status']
    

    return render_template('posts/details_post.html', post=post,answers=answers, user_likes=user_likes)

def posts_by_topic(topic_name):
    # Pastikan user terautentikasi
    # if 'username' not in session:
    #     return redirect(url_for('index'))
    
    user_id = session.get('user_id')
    topics = list(topics_collection.find())
    user_likes = set(str(like['post_id']) for like in likes_collection.find({"user_id": user_id}))
    recommendations = load_recommendations_by_topic(user_id, topic_name)
    recommendation_ids = [ObjectId(rec["_id"]) for rec in recommendations]
    posts = list(posts_collection.find({"_id": {"$nin": recommendation_ids}, "topic": topic_name}).sort("date", -1))
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
    return render_template('forum/forum.html', posts=posts,topics=topics, user_likes=user_likes, recommendations=recommendations)

def post_view():
    if 'username' not in session and session['role'] != 'admin':
        return redirect(url_for('login'))

    posts = list(posts_collection.find())
    # Join with user collection to get author details
    for post in posts:
        user = users_collection.find_one({"_id": ObjectId(post["id_user"])})
        post["author"] = user["username"] if user else "Unknown"

    return render_template('admin/features/posts.html', posts=posts)

def post_create(path, allowedFile):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    topics = list(topics_collection.find())
    
    if request.method == 'POST':
        title = request.form['title']
        question = request.form['question']
        topic = request.form['topic']
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        post_pic = None

        # Handle file upload
        if 'post_pic' in request.files:
            file = request.files['post_pic']
            if file and allowed_file(file.filename, allowedFile):
                filename = secure_filename(file.filename)
                datetime_prefix = datetime.now().strftime('%Y%m%d%H%M%S')
                filename = f"{datetime_prefix}_{filename}"
                file.save(os.path.join(path, filename))
                post_pic = filename

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
            "post_pic": post_pic  # This will be None if no file is uploaded
        })

        train_model()  # Update recommendations
        flash('Post created successfully!')
        return redirect(url_for('forum'))

    return render_template('posts/create_post.html', topics=topics)

def post_edit(post_id, path, allowedFile):
    if 'username' not in session:
        return redirect(url_for('login'))

    post = posts_collection.find_one({"_id": ObjectId(post_id)})

    if not post or post['id_user'] != session.get('user_id'):
        flash('You are not authorized to edit this post.')
        return redirect(url_for('forum'))

    topics = list(topics_collection.find())

    if request.method == 'POST':
        title = request.form['title']
        question = request.form['question']
        topic = request.form['topic']
        remove_pic = 'remove_pic' in request.form and request.form['remove_pic'] == 'on'
        post_pic = post.get('post_pic', '')  # Keep the old picture by default

        if remove_pic:
            post_pic = ''
            if post_pic:
                old_image_path = os.path.join(path, post_pic)
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)

        # Handle file upload
        if 'post_pic' in request.files:
            file = request.files['post_pic']
            if file and allowed_file(file.filename, allowedFile):
                filename = secure_filename(file.filename)
                datetime_prefix = datetime.now().strftime('%Y%m%d%H%M%S')
                filename = f"{datetime_prefix}_{filename}"

                # Remove the old image if it exists
                if post_pic:
                    old_image_path = os.path.join(path, post_pic)
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)

                # Save the new image
                file.save(os.path.join(path, filename))
                post_pic = filename

        if topic == 'new_topic':
            new_topic = request.form['new_topic']
            if not is_unique('name', new_topic, topics_collection):
                flash('Topic already exists')
                return render_template('posts/edit_post.html', post=post, topics=topics)
            else:
                topics_collection.insert_one({'name': new_topic})
                topic = new_topic

        posts_collection.update_one(
            {"_id": ObjectId(post_id)},
            {"$set": {"title": title, "question": question, "topic": topic, "post_pic": post_pic}}
        )

        flash('Post updated successfully!')
        return redirect(url_for('forum'))

    return render_template('posts/edit_post.html', post=post, topics=topics)


def post_delete(post_id,path):
    if 'username' not in session:
        return redirect(url_for('login'))
    post = posts_collection.find_one({"_id": ObjectId(post_id)})
    post_pic = post.get('post_pic', '')
    if post_pic:
        old_image_path = os.path.join(path, post_pic)
        if os.path.exists(old_image_path):
            os.remove(old_image_path)
    # Hapus post
    posts_collection.delete_one({"_id": ObjectId(post_id)})

    # Hapus likes terkait
    likes_collection.delete_many({"post_id": post_id})

    train_model()  # Update recommendations
    flash('Post deleted successfully!')
    if session['role'] != 'admin':
        return redirect(url_for('forum'))
    else:
        return redirect(url_for('view_posts'))


def post_like(post_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    user_id = session.get('user_id')
    if not likes_collection.find_one({"user_id": user_id, "post_id": post_id}):
        likes_collection.insert_one({"user_id": user_id, "post_id": post_id})
        train_model()  # Update recommendations
        post = posts_collection.find_one({"_id": ObjectId(post_id)})
        post['like_count'] = likes_collection.count_documents({"post_id": str(post['_id'])})

        return jsonify({"success": True, "like_count": post['like_count']}), 200
    else:
        return jsonify({"success": False, "message": "Post already liked"}), 400


def post_unlike(post_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    user_id = session.get('user_id')
    like = likes_collection.find_one({"user_id": user_id, "post_id": post_id})
    if like:
        likes_collection.delete_one({"_id": like['_id']})
        post = posts_collection.find_one({"_id": ObjectId(post_id)})
        post['like_count'] = likes_collection.count_documents({"post_id": str(post['_id'])})

        train_model()  # Update recommendations
        return jsonify({"success": True, "like_count": post['like_count']}), 200
    else:
        return jsonify({"success": False, "message": "Post not liked yet"}), 400
    

