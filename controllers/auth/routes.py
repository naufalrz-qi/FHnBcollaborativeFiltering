from flask import render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import bcrypt
from . import users_collection
from validation import validate_phone_number, is_unique, ensure_admin_exists  # Import the validation functions


def auth_login():
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

def auth_logout():
    session.pop('username', None)
    session.pop('user_id', None)
    return redirect(url_for('index'))
