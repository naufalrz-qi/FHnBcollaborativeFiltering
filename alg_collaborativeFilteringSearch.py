from pymongo import MongoClient
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from bson import ObjectId
import json

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017')
db = client['collaborativefilteringtest']  # Database name
users_collection = db['users']
posts_collection = db['posts']
likes_collection = db['likes']
answers_collection = db['answers']  # Add answers collection

def train_search_model(query):
    # Fetch data from MongoDB
    users = list(users_collection.find())
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
    posts = list(posts_collection.find(search_query))

    if not posts:
        posts = list(posts_collection.find())
        
    # Get likes for filtered posts
    post_ids = [str(post['_id']) for post in posts]
    likes = list(likes_collection.find({'post_id': {'$in': post_ids}}))
    # Get answers for filtered posts
    answers = list(answers_collection.find({'post_id': {'$in': post_ids}}))


    # Create mappings for user and post IDs (using string IDs)
    user_ids = {str(user['_id']): idx for idx, user in enumerate(users)}
    post_ids = {str(post['_id']): idx for idx, post in enumerate(posts)}

    print('post_id: ', post_ids , 'user_ids: ', user_ids)

    # Create rating matrix
    num_users = len(users)
    num_posts = len(posts)
    ratings_matrix = np.zeros((num_users, num_posts))

    for like in likes:
        user_id_str = str(like['user_id'])
        post_id_str = str(like['post_id'])

        # Debug output: Check if the ID exists in the mappings
        if user_id_str not in user_ids:
            print(f"User ID {user_id_str} not found in user_ids mapping")
            continue
        if post_id_str not in post_ids:
            print(f"Post ID {post_id_str} not found in post_ids mapping")
            continue

        user_idx = user_ids[user_id_str]
        post_idx = post_ids[post_id_str]

        ratings_matrix[user_idx, post_idx] = 1

    for answer in answers:
        user_id_str = str(answer['user_id'])
        post_id_str = str(answer['post_id'])

        # Debug output: Check if the ID exists in the mappings
        if user_id_str not in user_ids:
            print(f"User ID {user_id_str} not found in user_ids mapping")
            continue
        if post_id_str not in post_ids:
            print(f"Post ID {post_id_str} not found in post_ids mapping")
            continue

        user_idx = user_ids[user_id_str]
        post_idx = post_ids[post_id_str]

        ratings_matrix[user_idx, post_idx] += 1  # Increment for each answer

    print('INI RATING MATRIX:', ratings_matrix)

    # Calculate cosine similarity between users
    user_similarity = cosine_similarity(ratings_matrix)
    print('------------------------------------------------------')
    print('user similarity: ', user_similarity)
    print('------------------------------------------------------')

    # Function to recommend posts for a given user based on similar users' likes and answers
    def recommend_posts(user_idx, num_recommendations=3):
        sim_scores = user_similarity[user_idx]
        print('sim_scores: ', sim_scores)
        print('------------------------------------------------------')

        similar_users = np.argsort(sim_scores)[::-1][1:]  # Exclude the user itself
        print('similar users: ', similar_users)
        print('------------------------------------------------------')

        post_scores = np.zeros(num_posts)

        for similar_user in similar_users:
            post_scores += sim_scores[similar_user] * ratings_matrix[similar_user]

        post_scores[ratings_matrix[user_idx] > 0] = 0  # Zero out already liked or answered posts

        recommended_post_indices = np.argsort(post_scores)[::-1][:num_recommendations]
        return recommended_post_indices

    # Generate recommendations for all users and save to a dictionary
    recommendations = {}
    for user_id_str, user_idx in user_ids.items():
        recommended_posts = recommend_posts(user_idx, num_recommendations=3)
        print('------------------------------------------------------')
        print('search recommended posts: ', recommended_posts)
        print('------------------------------------------------------')
        recommended_post_ids = [list(post_ids.keys())[list(post_ids.values()).index(post_idx)] for post_idx in recommended_posts]
        recommendations[user_id_str] = recommended_post_ids

    # Save recommendations to a JSON file
    with open('search_recommendations.json', 'w') as f:
        json.dump(recommendations, f)

def search_posts(query, user_id):
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
    search_results = list(posts_collection.find(search_query))
    search_results_ids = [str(result['_id']) for result in search_results]

    if user_id:
        with open('search_recommendations.json', 'r') as f:
            recommendations = json.load(f)

        user_recommended_posts = recommendations.get(str(user_id), [])
        filtered_recommendations = [post for post in user_recommended_posts if post in search_results_ids]
        search_recommendations = list(posts_collection.find({"_id": {"$in": [ObjectId(post_id) for post_id in filtered_recommendations]}}))
        return search_recommendations
    else:
        return search_results
