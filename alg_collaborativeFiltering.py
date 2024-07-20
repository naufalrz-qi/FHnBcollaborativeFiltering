#!/usr/bin/env python
# coding: utf-8

# In[3]:


from pymongo import MongoClient
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from bson import ObjectId
import random
import json
import os

# Connect to MongoDB
mongo_uri = os.getenv('MONGO_URI')
client = MongoClient(mongo_uri)
db = client['collaborativefilteringtest']  # Database name
users_collection = db['users']
posts_collection = db['posts']
likes_collection = db['likes']


# In[4]:


# Fetch data from MongoDB
users = list(users_collection.find())
posts = list(posts_collection.find())
likes = list(likes_collection.find())


# Create mappings for user and post IDs (using string IDs)
user_ids = {str(user['_id']): idx for idx, user in enumerate(users)}
post_ids = {str(post['_id']): idx for idx, post in enumerate(posts)}


# Create rating matrix
num_users = len(users)
num_posts = len(posts)
ratings_matrix = np.zeros((num_users, num_posts))

for like in likes:
    user_id_str = like['user_id']
    post_id_str = like['post_id']
    
    # Debug output: Check if the ID exists in the mappings
    if user_id_str not in user_ids:
        print(f"User ID {user_id_str} not found in user_ids mapping")
    if post_id_str not in post_ids:
        print(f"Post ID {post_id_str} not found in post_ids mapping")

    user_idx = user_ids[user_id_str]
    post_idx = post_ids[post_id_str]
    ratings_matrix[user_idx, post_idx] = 1
    


# In[5]:


# Calculate cosine similarity between users
user_similarity = cosine_similarity(ratings_matrix)
print('------------------------------------------------------')
print('user similarity: ', user_similarity)
print('------------------------------------------------------')


# Function to recommend posts for a given user based on similar users' likes
def recommend_posts(user_idx, num_recommendations=5):
    sim_scores = user_similarity[user_idx]
    print('------------------------------------------------------')
    print('sim_scores: ', sim_scores)
    print('------------------------------------------------------')
    
    similar_users = np.argsort(sim_scores)[::-1][1:]  # Exclude the user itself
    print('------------------------------------------------------')
    print('similar users: ', similar_users)
    print('------------------------------------------------------')
    
    post_scores = np.zeros(num_posts)
    
    
    for similar_user in similar_users:
        post_scores += sim_scores[similar_user] * ratings_matrix[similar_user]

    print('------------------------------------------------------')
    print('post score: ', post_scores)
    print('------------------------------------------------------')
    post_scores[ratings_matrix[user_idx] > 0] = 0
    recommended_post_indices = np.argsort(post_scores)[::-1][:num_recommendations]
    return recommended_post_indices

# Generate recommendations for all users and save to a dictionary
recommendations = {}
for user_id_str, user_idx in user_ids.items():
    recommended_posts = recommend_posts(user_idx, num_recommendations=5)
    recommended_post_ids = [list(post_ids.keys())[list(post_ids.values()).index(post_idx)] for post_idx in recommended_posts]
    recommendations[user_id_str] = recommended_post_ids

# Save recommendations to a JSON file
with open('recommendations.json', 'w') as f:
    json.dump(recommendations, f)


# In[ ]:


def train_model():
    # Implementasi pelatihan model
    # Misalnya, menghasilkan recommendations.json
    recommendations = {}
    for user_id_str, user_idx in user_ids.items():
        recommended_posts = recommend_posts(user_idx, num_recommendations=10)
        print('------------------------------------------------------')
        print('recommended posts: ', recommended_posts)
        print('------------------------------------------------------')
        recommended_post_ids = [list(post_ids.keys())[list(post_ids.values()).index(post_idx)] for post_idx in recommended_posts]
        recommendations[user_id_str] = recommended_post_ids
    
    with open('recommendations.json', 'w') as f:
        json.dump(recommendations, f)
    print("Recommendations updated.")

