import os
from cornac.models import BiVAECF # Assuming this is the correct import
from cornac.data import Dataset, Reader # Import Dataset and Reader

import torch
import numpy as np
import torch
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import pickle
import convert
import random
from flask import jsonify, request

# --- Option 1: Use the Environment Variable ---
MODEL_PATH = os.environ.get("MODEL_PATH")
TRAIN_SET_PATH = os.environ.get("TRAIN_SET")

if not MODEL_PATH or not TRAIN_SET_PATH:
    print("Error: MODEL_PATH and TRAIN_SET environment variables must be set.")
    exit()

if not os.path.exists(MODEL_PATH):
    print(f"Error: Model file not found at {MODEL_PATH}")
    exit()

if not os.path.exists(TRAIN_SET_PATH):
    print(f"Error: Trainset file not found at {TRAIN_SET_PATH}")
    exit()

print(f"Loading model from: {MODEL_PATH}")
print(f"Loading train set from: {TRAIN_SET_PATH}")

bivae = BiVAECF.load(MODEL_PATH, trainable=False)

train_set = Dataset.load(TRAIN_SET_PATH)
print("Model and Train Set loaded successfully.")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
bivae.bivae.to(device)
print(f"Using device: {device}")

def closest_user(watchlist):
    """
    Finds the ID of the most similar existing user based on a new user's watchlist.

    Args:
        watchlist (dict): {raw_item_id: rating} for the new user.
        loaded_bivae_model (BiVAECF): The pre-loaded BiVAECF model instance.
        loaded_train_set (Dataset): The pre-loaded Cornac Dataset instance.

    Returns:
        str or int: The raw user ID of the most similar existing user,
                    or None if no valid interactions are found.
    """
    print(f"\nFinding closest user for watchlist: {watchlist}")

    global bivae, train_set

    loaded_bivae_model = bivae
    loaded_train_set = train_set

    # Use maps and info from the loaded train_set
    iid_map = loaded_train_set.iid_map
    user_ids = loaded_train_set.user_ids # List mapping internal idx to raw ID
    num_items = loaded_train_set.num_items

    # Prepare Input Vector for New User
    user_vector = np.zeros(num_items)
    valid_interactions = 0
    for item_id_raw, rating in watchlist.items():
        # Check if item exists in the train_set's item map
        if item_id_raw in iid_map:
            item_idx = iid_map[item_id_raw] # Get internal index
            # Ensure index is within bounds (should be if map is correct)
            if 0 <= item_idx < num_items:
                 user_vector[item_idx] = 1.0 # Binarize interaction
                 valid_interactions += 1
            else:
                 print(f"Warning: Item ID {item_id_raw} mapped to invalid index {item_idx}. Skipping.")
        else:
            print(f"Warning: Item ID {item_id_raw} not in training set item map. Skipping.")

    if valid_interactions == 0:
        print("Error: New user has no interactions with items known to the model.")
        return None # Indicate failure

    user_vector_tensor = torch.tensor(user_vector, dtype=torch.float32).unsqueeze(0)
    user_vector_tensor = user_vector_tensor.to(device) # Move to device

    # Get New User Embedding
    internal_torch_model = loaded_bivae_model.bivae
    with torch.no_grad():
        # Use the user encoder part of the loaded BiVAE model
        new_user_mean, _ = internal_torch_model.encode_user(user_vector_tensor)
        new_user_embedding = new_user_mean.cpu().numpy() # Get embedding on CPU as numpy array

    # Get Existing User Embeddings
    # Access the learned user means (mu_theta) from the loaded BiVAE model
    existing_user_embeddings = internal_torch_model.mu_theta.cpu().detach().numpy()

    # Sanity check (optional but good)
    if existing_user_embeddings.shape[0] != loaded_train_set.num_users:
         print(f"Warning: Mismatch between train_set user count ({loaded_train_set.num_users}) "
               f"and embedding count ({existing_user_embeddings.shape[0]})")

    # Calculate Similarities
    similarities = cosine_similarity(new_user_embedding, existing_user_embeddings)[0]

    # Find Most Similar User index
    most_similar_user_internal_idx = np.argmax(similarities)
    max_similarity = similarities[most_similar_user_internal_idx]

    # Map internal index back to raw user ID using train_set.user_ids
    if 0 <= most_similar_user_internal_idx < len(user_ids):
        most_similar_user_id_raw = user_ids[most_similar_user_internal_idx]
        print(f"Most similar existing user found: ID={most_similar_user_id_raw}, Similarity={max_similarity:.4f}")
        return most_similar_user_id_raw
    else:
        # This case should ideally not happen if indices are correct
        print(f"Error: Calculated most similar user index ({most_similar_user_internal_idx}) is out of bounds for user_ids list (len={len(user_ids)}).")
        return None # Indicate failure


def recommendation_ids(user_id, num=10):
    print(f"Generating {num} recommendations for user: {user_id}")
    
    if user_id not in train_set.uid_map:
         print(f"Warning: User ID '{user_id}' not found in the original training set map.")

    recs = bivae.recommend(user_id=user_id, k=num, remove_seen=True, train_set=train_set)
    return recs

if __name__ == "__main__":
    new_user_history = {
        242: 4.0,  # Contact (1997)
        50: 5.0,  # Star Wars (1977)
        181: 4.0,  # Return of the Jedi (1983)
        100: 5.0,  # Fargo (1996)
        7:  3.0   # Twelve Monkeys (1995)
    }

    closest = closest_user(new_user_history)  
    print(f"Closest user ID: {closest}")

    recs = recommendation_ids(closest, num=5)
    print(recs)

    titles = convert.titles_from_recs(recs)
    print(titles)   