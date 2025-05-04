import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


def calculate_cosine_similarity(vec1, vec2):
    """Calculate cosine similarity between two vectors"""
    if not isinstance(vec1, np.ndarray):
        vec1 = np.array(vec1).reshape(1, -1)
    if not isinstance(vec2, np.ndarray):
        vec2 = np.array(vec2).reshape(1, -1)
    
    return cosine_similarity(vec1, vec2)[0][0]


def find_similar_movies(movies_df, query_embedding, top_n=50, threshold=0.6):
    """
    Find movies with similar overview embeddings to the query embedding
    
    Args:
        movies_df: DataFrame containing movies with embeddings
        query_embedding: The embedding to compare against
        top_n: Number of top similar movies to return
        threshold: Minimum similarity score to consider
    
    Returns:
        DataFrame with similar movies and similarity scores
    """
    # Ensure query_embedding is the right shape
    query_embedding = np.array(query_embedding).reshape(1, -1)
    
    # Calculate similarity for each movie
    similarities = []
    for idx, row in movies_df.iterrows():
        movie_embedding = row['overview_embedding']
        if movie_embedding is not None and len(movie_embedding) > 0:
            try:
                similarity = calculate_cosine_similarity(query_embedding, movie_embedding)
                similarities.append((idx, similarity))
            except:
                similarities.append((idx, 0))
        else:
            similarities.append((idx, 0))
    
    # Sort by similarity score
    similarities.sort(key=lambda x: x[1], reverse=True)
    
    # Get indices of top similar movies that meet threshold
    top_indices = [idx for idx, score in similarities if score >= threshold][:top_n]
    
    # Create result dataframe
    result_df = movies_df.loc[top_indices].copy()
    
    # Add similarity scores
    similarity_scores = [score for idx, score in similarities if idx in top_indices]
    result_df['similarity_score'] = similarity_scores
    
    return result_df.sort_values('similarity_score', ascending=False)