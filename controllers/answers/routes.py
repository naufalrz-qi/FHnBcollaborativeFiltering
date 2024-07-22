from flask import render_template,jsonify, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from . import users_collection, topics_collection, posts_collection, likes_collection, answers_collection
import os
from bson import ObjectId
from datetime import datetime
from alg_collaborativeFiltering import train_model
from validation import validate_phone_number, is_unique, ensure_admin_exists, allowed_file

from flask import jsonify

def answer_create(post_id, path, allowedFile):
    if 'username' not in session:
        return redirect(url_for('index'))

    user_id = session.get('user_id')
    answer_content = request.form['answer']
    answer_pic = None

    # Handle file upload
    if 'answer_pic' in request.files:
        file = request.files['answer_pic']
        if file and allowed_file(file.filename, allowedFile):
            filename = secure_filename(file.filename)
            datetime_prefix = datetime.now().strftime('%Y%m%d%H%M%S')
            filename = f"{datetime_prefix}_{filename}"
            file.save(os.path.join(path, filename))
            answer_pic = filename

    if not answer_content:
        return jsonify(success=False, message='Answer content cannot be empty')

    
    answer = {
        "post_id": str(post_id),
        "user_id": user_id,
        "content": answer_content,
        "answer_pic": answer_pic,
        "date": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    result=answers_collection.insert_one(answer)
    answer['_id'] = str(result.inserted_id)
    answer['username'] = session.get('username')
    answer['answer_pic'] = url_for('static', filename='uploads/answer/img/' + answer_pic) if answer_pic else None
# Convert ObjectId fields to strings
    answer['post_id'] = str(answer['post_id'])
    answer['user_id'] = str(answer['user_id'])
    

    return jsonify(success=True, answer=answer)

