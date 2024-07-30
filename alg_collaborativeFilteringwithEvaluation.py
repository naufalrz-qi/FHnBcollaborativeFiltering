from pymongo import MongoClient
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
import pandas as pd
import json
import random
import os
from dotenv import load_dotenv

load_dotenv()
mongo_uri = os.getenv('MONGO_URI')
client = MongoClient(mongo_uri)
db = client[os.getenv('MONGO_DB_NAME')]

users_collection = db['users']
posts_collection = db['posts']
likes_collection = db['likes']
answers_collection = db['answers']  # Add answers collection

def train_model():
    # Fetch data from MongoDB
    users = list(users_collection.find())
    posts = list(posts_collection.find())
    likes = list(likes_collection.find())
    answers = list(answers_collection.find())  # Fetch answers

    # Create mappings for user and post IDs (using string IDs)
    user_ids = {str(user['_id']): idx for idx, user in enumerate(users)}
    post_ids = {str(post['_id']): idx for idx, post in enumerate(posts)}

    # Create rating matrix
    num_users = len(users)
    num_posts = len(posts)
    ratings_matrix = np.zeros((num_users, num_posts))
    
    # Create a mapping for post topics
    post_topics = {str(post['_id']): post['topic'] for post in posts}

    for like in likes:
        user_id_str = str(like['user_id'])
        post_id_str = str(like['post_id'])
        
        if user_id_str not in user_ids:
            print(f"User ID {user_id_str} not found in user_ids mapping")
        if post_id_str not in post_ids:
            print(f"Post ID {post_id_str} not found in post_ids mapping")

        user_idx = user_ids[user_id_str]
        post_idx = post_ids[post_id_str]
        
        ratings_matrix[user_idx, post_idx] = 1

    for answer in answers:
        user_id_str = str(answer['user_id'])
        post_id_str = str(answer['post_id'])
        
        if user_id_str not in user_ids:
            print(f"User ID {user_id_str} not found in user_ids mapping")
        if post_id_str not in post_ids:
            print(f"Post ID {post_id_str} not found in post_ids mapping")

        user_idx = user_ids[user_id_str]
        post_idx = post_ids[post_id_str]
        
        ratings_matrix[user_idx, post_idx] = 1

    # Build user-topic profiles
    user_topic_preferences = {user_idx: {} for user_idx in range(num_users)}

    for user_idx, user_interactions in enumerate(ratings_matrix):
        liked_posts = np.where(user_interactions > 0)[0]
        for post_idx in liked_posts:
            topic = post_topics[list(post_ids.keys())[post_idx]]
            if topic in user_topic_preferences[user_idx]:
                user_topic_preferences[user_idx][topic] += 1
            else:
                user_topic_preferences[user_idx][topic] = 1

    # Normalize topic preferences
    for user_idx in user_topic_preferences:
        total_likes = sum(user_topic_preferences[user_idx].values())
        for topic in user_topic_preferences[user_idx]:
            user_topic_preferences[user_idx][topic] /= total_likes

    def create_train_test_split(ratings_matrix, test_size=0.2):
        num_users, num_posts = ratings_matrix.shape
        train_matrix = np.copy(ratings_matrix)
        test_matrix = np.zeros_like(ratings_matrix)

        for user in range(num_users):
            non_zero_indices = np.nonzero(ratings_matrix[user])[0]
            
            if len(non_zero_indices) < 2:
                continue
            
            train_indices, test_indices = train_test_split(non_zero_indices, test_size=test_size, random_state=42)
            
            train_matrix[user, train_indices] = ratings_matrix[user, train_indices]
            test_matrix[user, test_indices] = ratings_matrix[user, test_indices]

        return train_matrix, test_matrix

    # Train-test split
    train_matrix, test_matrix = create_train_test_split(ratings_matrix, test_size=0.2)

    # Calculate cosine similarity between users
    user_similarity = cosine_similarity(train_matrix)
    
    # Function to recommend posts for a given user based on similar users' likes and topic preferences
    def recommend_posts(user_idx, num_recommendations=5):
        sim_scores = user_similarity[user_idx]
        similar_users = np.argsort(sim_scores)[::-1][1:]

        post_scores = np.zeros(num_posts)
    
        for similar_user in similar_users:
            post_scores += sim_scores[similar_user] * train_matrix[similar_user]

        # Incorporate topic preferences into the scoring
        for post_idx in range(num_posts):
            post_id_str = list(post_ids.keys())[post_idx]
            topic = post_topics[post_id_str]
            if topic in user_topic_preferences[user_idx]:
                post_scores[post_idx] *= (1 + user_topic_preferences[user_idx][topic])

        post_scores[train_matrix[user_idx] > 0] = 0
        recommended_post_indices = np.argsort(post_scores)[::-1][:num_recommendations]
        return recommended_post_indices

    # Generate recommendations for all users and save to a dictionary
    recommendations = {}
    for user_id_str, user_idx in user_ids.items():
        if user_idx >= user_similarity.shape[0]:
            print(f"User index {user_idx} is out of bounds for user_similarity with shape {user_similarity.shape}")
            continue
        recommended_posts = recommend_posts(user_idx, num_recommendations=5)
        print('------------------------------------------------------')
        print('recommended posts: ', recommended_posts)
        print('------------------------------------------------------')
        recommended_post_ids = [list(post_ids.keys())[list(post_ids.values()).index(post_idx)] for post_idx in recommended_posts]
        recommendations[user_id_str] = recommended_post_ids

    # Save recommendations to a JSON file
    with open('recommendations.json', 'w') as f:
        json.dump(recommendations, f)

    # Evaluate model
    actual_ratings = []
    predicted_ratings = []

    for user_idx in range(len(test_matrix)):
        for post_idx in range(num_posts):
            if test_matrix[user_idx, post_idx] != 0:
                actual_ratings.append(test_matrix[user_idx, post_idx])
                predicted_ratings.append(predict_rating(user_idx, post_idx, train_matrix, user_similarity))

    if len(actual_ratings) == 0 or len(predicted_ratings) == 0:
        print("Warning: Salah satu atau kedua array kosong.")
        return None

    mae = mean_absolute_error(actual_ratings, predicted_ratings)
    print(f'Mean Absolute Error: {mae}')

    return train_matrix, recommendations, user_similarity

def predict_rating(user_idx, post_idx, train_matrix, user_similarity):
    sim_scores = user_similarity[user_idx]
    item_ratings = train_matrix[:, post_idx]
    non_zero_ratings = item_ratings[item_ratings != 0]

    weighted_sum = 0
    similarity_sum = 0
    for idx in range(len(non_zero_ratings)):
        similarity = sim_scores[idx]
        weighted_sum += similarity * item_ratings[idx]
        similarity_sum += similarity

    if similarity_sum == 0:
        return 0
    return weighted_sum / similarity_sum

def visualize_recommendations(recommendations):
    recommendations_df = pd.DataFrame.from_dict(recommendations, orient='index')

    unique_recommendations_count = recommendations_df.apply(lambda x: len(set(x.dropna())), axis=1)
    print("Distribution of Unique Recommendations per User:")
    print(unique_recommendations_count.describe())

    user_sample = random.sample(list(recommendations.keys()), 5)
    for user_id in user_sample:
        print(f"Recommendations for user {user_id}: {recommendations[user_id]}")

    all_recommendations = recommendations_df.values.flatten()
    post_counts = pd.Series(all_recommendations).value_counts()

    print("Distribution of Recommendations per Post:")
    print(post_counts.describe())

def visualize_user_similarity(user_similarity):
    similarity_scores = user_similarity.flatten()
    print("Distribution of User Similarities:")
    print(pd.Series(similarity_scores).describe())

# Train the model
result = train_model()

if result is not None:
    train_matrix, recommendations, user_similarity = result
    visualize_recommendations(recommendations)
    visualize_user_similarity(user_similarity)
else:
    print("Gagal melatih model. Tidak dapat melanjutkan.")
