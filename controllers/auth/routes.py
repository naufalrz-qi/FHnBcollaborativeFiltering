from flask import render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import bcrypt
from datetime import datetime
import os
from bson import ObjectId
from . import users_collection, posts_collection
from validation import validate_phone_number, is_unique, ensure_admin_exists  # Import the validation functions


def auth_login():
    if request.method == 'POST':
        username = request.form['username'].lower()  # Convert to lowercase
        password = request.form['password']
        user = users_collection.find_one({"username": username})
        print(user)
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
            session['username'] = username
            session['name'] = user['profile_name']
            session['photo'] = user['profile_pic']
            session['role'] = user['role']
            session['user_id'] = str(user['_id'])  # Store user ID in session
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('forum'))
        else:
            flash('Invalid username/password combination')

    return render_template('auth/login.html')

def auth_profile(user_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Ambil user berdasarkan user_id
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        flash('User not found.')
        return redirect(url_for('index'))
    
    # Pastikan user memiliki peran 'normal' atau 'expert'
    if user['role'] not in ['normal', 'expert']:
        flash('You do not have permission to view this profile.')
        return redirect(url_for('index'))

    # Ambil post yang dibuat oleh user
    posts = posts_collection.find({"id_user": str(user['_id'])})

    return render_template('auth/profile.html', user=user, posts=posts)


def auth_register():
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

# Fungsi untuk menyimpan file gambar
def save_profile_pic(profile_pic):
    if profile_pic:
        filename = secure_filename(profile_pic.filename)
        datetime_prefix = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f"{datetime_prefix}_{filename}"
        profile_pic_path = os.path.join('static/uploads/profile_pics', filename)
        profile_pic.save(profile_pic_path)
        return profile_pic_path
    return None

# Fungsi untuk menghapus file gambar
def delete_profile_pic(profile_pic_path):
    if os.path.exists(profile_pic_path):
        os.remove(profile_pic_path)
        
# @settings_bp.route('/settings', methods=['GET', 'POST'])
def auth_settings():
    if 'user_id' not in session:
        flash('Please log in to access settings', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']
    user = users_collection.find_one({'_id': ObjectId(user_id)})
    print(user)

    if request.method == 'POST':
        username = request.form.get('username').lower()
        email = request.form.get('email')
        phone_number = request.form.get('phone_number')
        profile_name = request.form.get('profile_name')
        gender = request.form.get('gender')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        profile_pic = request.files.get('profile_pic')
        

        if not bcrypt.checkpw(current_password.encode('utf-8'), user['password']):
            flash('Current password is incorrect', 'danger')
            return redirect(url_for('settings'))

        if user['username']!=username and not is_unique('username', username, users_collection):
            flash('Username is already taken', 'danger')
            return redirect(url_for('settings'))

        if user['email']!=email and not is_unique('email', email, users_collection):
            flash('Email is already registered', 'danger')
            return redirect(url_for('settings'))

        if user['phone_number']!=phone_number and not is_unique('phone_number', phone_number, users_collection):
            flash('Phone number is already registered', 'danger')
            return redirect(url_for('settings'))

        if not validate_phone_number(phone_number):
            flash('Invalid phone number format', 'danger')
            return redirect(url_for('settings'))

        update_data = {
            'username': username,
            'email': email,
            'phone_number': phone_number,
            'profile_name': profile_name,
            'gender': gender
        }

        if new_password:
            update_data['password'] = generate_password_hash(new_password)

        if profile_pic:
            profile_pic_path = save_profile_pic(profile_pic)
            if profile_pic_path:
                if user.get('profile_pic'):
                    delete_profile_pic(user['profile_pic'])
                update_data['profile_pic'] = profile_pic_path
                session['photo'] = profile_pic_path

        users_collection.update_one({'_id': ObjectId(user_id)}, {'$set': update_data})
        
        flash('Settings updated successfully', 'success')
        return redirect(url_for('settings'))

    return render_template('auth/settings.html', user=user)

def auth_logout():
    session.clear()
    return redirect(url_for('index'))
