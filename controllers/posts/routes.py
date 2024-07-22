from flask import render_template,jsonify, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from . import users_collection, topics_collection, posts_collection, likes_collection
import os
from bson import ObjectId
from datetime import datetime
from alg_collaborativeFiltering import train_model
from validation import validate_phone_number, is_unique, ensure_admin_exists, allowed_file
from controllers.algorithm.routes import load_recommendations_by_topic

def posts_by_topic(topic_name):
    # Pastikan user terautentikasi
    if 'username' not in session:
        return redirect(url_for('index'))
    
    user_id = session.get('user_id')
    user_likes = set(str(like['post_id']) for like in likes_collection.find({"user_id": user_id}))
    posts = list(posts_collection.find({"topic": topic_name}).sort("date", -1))
    print(posts)
    user = users_collection.find_one({'_id':ObjectId(user_id)})
    profilename= user['profile_name']
    # Fetch the number of likes for each post
    for post in posts:
        post['like_count'] = likes_collection.count_documents({"post_id": str(post['_id'])})
        post['_id'] = str(post['_id'])  # Pastikan _id diubah menjadi string
    # Temukan semua post yang sesuai dengan topik yang diberikan
    recommendations = load_recommendations_by_topic(user_id, topic_name)
    return render_template('forum/forum.html', posts=posts,profilename=profilename, user_likes=user_likes, recommendations=recommendations)


def post_create(path, allowedFile):
    if 'username' not in session:
        return redirect(url_for('index'))
    
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
        post_pic = post.get('post_pic', '')  # Keep the old picture by default

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



def post_like(post_id):
    if 'username' not in session:
        return redirect(url_for('index'))

    print('=========================================')
    print('INI ADALAH :',post_id)
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
        return redirect(url_for('index'))

    user_id = session.get('user_id')
    print('=========================================')
    print('INI ADALAH :',post_id)    
    like = likes_collection.find_one({"user_id": user_id, "post_id": post_id})
    if like:
        likes_collection.delete_one({"_id": like['_id']})
        post = posts_collection.find_one({"_id": ObjectId(post_id)})
        post['like_count'] = likes_collection.count_documents({"post_id": str(post['_id'])})

        train_model()  # Update recommendations
        return jsonify({"success": True, "like_count": post['like_count']}), 200
    else:
        return jsonify({"success": False, "message": "Post not liked yet"}), 400
