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

def answer_edit(answer_id,path, allowedFile):
    if 'username' not in session:
        return redirect(url_for('index'))

    answer = answers_collection.find_one({"_id": ObjectId(answer_id)})

    if not answer or answer['user_id'] != session.get('user_id'):
        flash('You are not authorized to edit this answer.')
        return redirect(url_for('forum'))

    post_id = answer['post_id']

    if request.method == 'POST':
        content = request.form['content']
        remove_pic = 'remove_pic' in request.form and request.form['remove_pic'] == 'on'
        answer_pic = answer.get('answer_pic', '')  # Keep the old picture by default

        if remove_pic:
            answer_pic = ''
            if answer_pic:
                old_image_path = os.path.join(path, answer_pic)
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)

        # Handle file upload
        if 'answer_pic' in request.files:
            file = request.files['answer_pic']
            if file and allowed_file(file.filename, allowedFile):
                filename = secure_filename(file.filename)
                datetime_prefix = datetime.now().strftime('%Y%m%d%H%M%S')
                filename = f"{datetime_prefix}_{filename}"

                # Remove the old image if it exists
                if answer_pic:
                    old_image_path = os.path.join(path, answer_pic)
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)

                # Save the new image
                file.save(os.path.join(path, filename))
                answer_pic = filename

        answers_collection.update_one(
            {"_id": ObjectId(answer_id)},
            {"$set": {"content": content, "answer_pic": answer_pic}}
        )

        flash('Answer updated successfully!')
        return redirect(url_for('post_details', post_id=post_id))

    return render_template('edit_answer.html', answer=answer)

def answer_delete(answer_id, path):
    answer = answers_collection.find_one({"_id": ObjectId(answer_id)})
    answer_pic = answer.get('answer_pic', '')
    if answer_pic:
        old_image_path = os.path.join(path, answer_pic)
        if os.path.exists(old_image_path):
            os.remove(old_image_path)
            
    if not answer:
        flash('Answer not found', 'danger')
        return redirect(url_for('index'))

    answers_collection.delete_one({"_id": ObjectId(answer_id)})
    flash('Answer deleted successfully', 'success')
    return redirect(url_for('post_details', post_id=answer['post_id']))