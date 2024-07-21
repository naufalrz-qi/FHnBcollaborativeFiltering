from flask import render_template,jsonify, request, redirect, url_for, session, flash
from . import users_collection, topics_collection, posts_collection, likes_collection
import os
from bson import ObjectId
from datetime import datetime
from alg_collaborativeFiltering import train_model
from validation import validate_phone_number, is_unique, ensure_admin_exists  # Import the validation functions

def post_create():
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

def post_delete(post_id):
    if 'username' not in session:
        return redirect(url_for('index'))

    # Hapus post
    posts_collection.delete_one({"_id": ObjectId(post_id)})

    # Hapus likes terkait
    likes_collection.delete_many({"post_id": post_id})

    train_model()  # Update recommendations
    flash('Post deleted successfully!')
    return redirect(url_for('forum'))

def post_edit(post_id):
    if 'username' not in session:
        return redirect(url_for('index'))

    post = posts_collection.find_one({"_id": ObjectId(post_id)})

    if not post or post['id_user'] != session.get('user_id'):
        flash('You are not authorized to edit this post.')
        return redirect(url_for('forum'))

    topics = list(topics_collection.find())

    if request.method == 'POST':
        title = request.form['title']
        question = request.form['question']
        topic = request.form['topic']
        post_pic = request.form.get('post_pic', '')

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

def post_like(post_id):
    if 'username' not in session:
        return redirect(url_for('index'))

    user_id = session.get('user_id')
    if not likes_collection.find_one({"user_id": user_id, "post_id": post_id}):
        likes_collection.insert_one({"user_id": user_id, "post_id": post_id})
        post = posts_collection.find_one({"_id": ObjectId(post_id)})
        posts_collection.update_one({"_id": ObjectId(post_id)}, {"$inc": {"like_count": 1}})
        train_model()  # Update recommendations
        return jsonify({"success": True, "like_count": post['like_count'] + 1}), 200
    else:
        return jsonify({"success": False, "message": "Post already liked"}), 400

def post_unlike(post_id):
    if 'username' not in session:
        return redirect(url_for('index'))

    user_id = session.get('user_id')
    like = likes_collection.find_one({"user_id": user_id, "post_id": post_id})
    if like:
        likes_collection.delete_one({"_id": like['_id']})
        post = posts_collection.find_one({"_id": ObjectId(post_id)})
        posts_collection.update_one({"_id": ObjectId(post_id)}, {"$inc": {"like_count": -1}})
        train_model()  # Update recommendations
        return jsonify({"success": True, "like_count": post['like_count'] - 1}), 200
    else:
        return jsonify({"success": False, "message": "Post not liked yet"}), 400