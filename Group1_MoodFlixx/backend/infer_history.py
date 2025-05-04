import os
import sys
import torch
import cornac
from embeddings_hist import *

from recommenders.datasets import movielens
from recommenders.datasets.python_splitters import python_random_split

from recommenders.models.cornac.cornac_utils import predict_ranking,predict
from recommenders.utils.timer import Timer
from recommenders.utils.constants import SEED
from recommenders.evaluation.python_evaluation import (
    map,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
)
from recommenders.utils.notebook_utils import store_metadata
from embeddings_hist import bivae, train_set

# Select MovieLens data size: 100k, 1m, 10m, or 20m
MOVIELENS_DATA_SIZE = '100k'

# top k items to recommend
TOP_K = 10

# Model parameters
LATENT_DIM = 50
ENCODER_DIMS = [100]
ACT_FUNC = "tanh"
LIKELIHOOD = "pois"
NUM_EPOCHS = 500
BATCH_SIZE = 128
LEARNING_RATE = 0.001


df = movielens.load_pandas_df(size=MOVIELENS_DATA_SIZE,title_col='title')
data = movielens.load_pandas_df(
    size=MOVIELENS_DATA_SIZE,
    header=["userID", "itemID", "rating"]
)



import numpy as np
import torch
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
from recommenders.utils.timer import Timer # Assuming Timer is used as before


def get_movie_reccs(titles_reviews):

    TOP_K = 10

    ids_reviews = {}
    for i in titles_reviews:
        item_title_to_id = df[['itemID', 'title']].drop_duplicates()
        item_title_to_id = item_title_to_id.set_index('title')['itemID'].to_dict()
        temp = item_title_to_id.get(i['title'], "Unknown")
        ids_reviews[temp] = i[1]


    # new_user_history = {
    #     242: 4.0,  # Contact (1997)
    #      50: 5.0,  # Star Wars (1977)
    #     181: 4.0,  # Return of the Jedi (1983)
    #     100: 5.0,  # Fargo (1996)
    #      7:  3.0   # Twelve Monkeys (1995)
    # }
    new_user_history = ids_reviews
    # print(f"New user history (raw item IDs): {new_user_history}")

    num_items = train_set.num_items
    user_vector = np.zeros(num_items)
    valid_interactions = 0
    known_raw_item_ids = set(train_set.item_ids) # Set for faster lookup

    for item_id_raw, rating in new_user_history.items():
        if item_id_raw in train_set.iid_map: # Check if item is known
            item_idx = train_set.iid_map[item_id_raw] # Get internal index
            # Binarize input for BiVAE as done in the internal learn function
            user_vector[item_idx] = 1.0 # Use 1.0 for interactions
            valid_interactions += 1

    if valid_interactions == 0:
        # Handle this case (e.g., recommend popular items)
        exit() # Example exit

    # Convert to the format expected by the encoder (PyTorch tensor)
    user_vector_tensor = torch.tensor(user_vector, dtype=torch.float32).unsqueeze(0) # Add batch dimension

    # Ensure tensor is on the correct device (CPU or GPU) using the recommender's device attribute
    device = bivae.device
    user_vector_tensor = user_vector_tensor.to(device)


    # 3. Get the New User's Latent Embedding (using the user encoder)
    # Access the internal PyTorch model via the 'bivae' attribute of the recommender
    internal_model = bivae.bivae
    internal_model.eval() # Set the internal model to evaluation mode
    with torch.no_grad(): # No need to compute gradients
    # Use the encode_user method which returns mu and std
        new_user_mean, new_user_std = internal_model.encode_user(user_vector_tensor)
        # Use the mean as the representative embedding
        new_user_embedding = new_user_mean.cpu().numpy()



    # 4. Get Existing User Embeddings
    #    The 'learn' function stores the inferred means in bivae.mu_theta
    existing_user_embeddings = bivae.bivae.mu_theta.cpu().detach().numpy()
    num_existing_users = existing_user_embeddings.shape[0]


    # 5. Calculate Similarities
    similarities = cosine_similarity(new_user_embedding, existing_user_embeddings)[0]


    # 6. Find the Most Similar User
    most_similar_user_idx = np.argmax(similarities) # Internal index
    max_similarity = similarities[most_similar_user_idx]

    # Convert internal user index back to original userID using the user_ids list
    if 0 <= most_similar_user_idx < len(train_set.user_ids):
        most_similar_user_id_raw = train_set.user_ids[most_similar_user_idx]
    else:
        exit()


    # 7. Generate Recommendations for the Similar User (Using Cornac's score method)

    # --- Option 1: Use the score method (predicts scores for all items) ---
    with Timer() as t_pred_sim:
    # Get scores for the similar user for ALL known items
    # The score method uses the learned mu_theta and mu_beta internally
        all_item_scores = bivae.score(most_similar_user_idx) # Pass internal index

        # Get items already seen by the *similar* user from the training data
        seen_items_raw = train[train['userID'] == most_similar_user_id_raw]['itemID'].tolist()
        seen_items_indices = [train_set.iid_map[iid] for iid in seen_items_raw if iid in train_set.iid_map]

        # Remove seen items by setting their scores very low
        if all_item_scores is not None: # Add a check in case scoring fails
            all_item_scores[seen_items_indices] = -np.inf

            # Get the internal indices of items sorted by score (highest first)
            ranked_item_indices = np.argsort(all_item_scores)[::-1]

            # Get the top K recommended item indices
            top_k_item_indices = ranked_item_indices[:TOP_K]

            # Map internal indices back to raw item IDs
            top_k_item_ids = [train_set.item_ids[idx] for idx in top_k_item_indices]
            top_k_scores = all_item_scores[top_k_item_indices]

            # Create a DataFrame for the results
            recommendations_df = pd.DataFrame({
                'userID': most_similar_user_id_raw, # Recommendations are *based on* this user
                'itemID': top_k_item_ids,
                'prediction': top_k_scores
            })
        else:
            recommendations_df = pd.DataFrame(columns=['userID', 'itemID', 'prediction']) # Empty df


        # --- Option 2: (Alternative) Use predict_ranking - Might be simpler if it works ---
        # You could also try using the original predict_ranking function, but ensure
        # you pass the *BiVAECF* recommender object, not the internal PyTorch one.
        # with Timer() as t_pred_sim_alt:
        #      recommendations_df_alt = predict_ranking(
        #          bivae_recommender, # Pass the Cornac recommender object
        #          train,             # Use original training DataFrame
        #          usercol='userID',
        #          itemcol='itemID',
        #          remove_seen=True,
        #          filter_by='user',
        #          users=[most_similar_user_id_raw] # Filter for the specific similar user
        #      ).head(TOP_K)
        # print(f"Took {t_pred_sim_alt} seconds for prediction (alt method).")
        # print("Alt method results:")
        # print(recommendations_df_alt)
        # Use recommendations_df from Option 1 or recommendations_df_alt from Option 2


        # 8. Present Recommendations to the New User

        # Optional: Map item IDs back to titles
    try:
    # Ensure df exists and has the necessary columns
        if 'df' in locals() and isinstance(df, pd.DataFrame) and all(c in df.columns for c in ['itemID', 'title']):
            item_id_to_title = df[['itemID', 'title']].drop_duplicates().set_index('itemID')['title'].to_dict()
            recommendations_df['title'] = recommendations_df['itemID'].map(item_id_to_title).fillna("Unknown Title")

    except Exception as e:
            print(f"An error occurred during title mapping: {e}")
            print(recommendations_df)


        #function which stores top 5 movie titles from the df
    return recommendations_df

def get_output(recommendations_df):
    # Get the top 5 movie titles from the recommendations DataFrame
    top_title = recommendations_df.head(1)['title'].tolist()

    return top_title