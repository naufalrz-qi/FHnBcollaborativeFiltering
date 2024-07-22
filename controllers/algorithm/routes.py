from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
from bson import ObjectId
from . import users_collection, posts_collection, likes_collection

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
            post['like_count'] = likes_collection.count_documents({"post_id": str(post['_id'])})
            post['_id'] = str(post['_id'])  # Pastikan _id diubah menjadi string
            recommended_posts.append(post)
    
    return recommended_posts

def load_recommendations_by_topic(user_id,topic):
    with open('recommendations.json', 'r') as file:
        recommendations_data = json.load(file)
    
    # Ambil rekomendasi untuk user saat ini
    recommended_post_ids = recommendations_data.get(str(user_id), [])
    
    # Ambil informasi postingan dari database
    recommended_posts = []
    for post_id in recommended_post_ids:
        post = posts_collection.find_one({"_id": ObjectId(post_id), "topic":topic})
        if post:
            post['like_count'] = likes_collection.count_documents({"post_id": str(post['_id'])})
            post['_id'] = str(post['_id'])  # Pastikan _id diubah menjadi string
            recommended_posts.append(post)
    
    return recommended_posts
