import pandas as pd
import faiss
import numpy as np

df = pd.read_csv('movies.csv')
movie_metadata = {
    i: {
        "title": row["title"],
        "popularity": row["popularity"],
        "runtime": row["runtime"],
        "original_language": row["original_language"],
        "genres": row["genres"],
    }
    for i, row in df.iterrows()
}


def query_movies_by_emotion(mood_vector, top_k=1000, index_path="movie_emotion_index.faiss"):
    # Load the FAISS index
    index = faiss.read_index(index_path)  # load the index.
    mood_vector = np.array(mood_vector, dtype='float32').reshape(1, -1)
    faiss.normalize_L2(mood_vector)
    distances, indices = index.search(mood_vector, top_k)
    results = df.iloc[indices[0]].copy()
    results['score'] = distances[0]
    return results[['title','popularity','runtime','genres','original_language','score']]



def query_movies_ensemble(user_mood_embedding, user_semantic_embedding, user_tagline_embedding, top_k=1000, weight_mood=0.0, weight_semantic=0.0, weight_tagline=1.0):
    # Ensure proper shape and dtype
    user_mood_embedding = np.array(user_mood_embedding, dtype='float32').reshape(1, -1)
    user_semantic_embedding = np.array(user_semantic_embedding, dtype='float32').reshape(1, -1)
    user_tagline_embedding = np.array(user_tagline_embedding, dtype='float32').reshape(1, -1)
    faiss.normalize_L2(user_mood_embedding)
    faiss.normalize_L2(user_semantic_embedding)
    faiss.normalize_L2(user_tagline_embedding)
    # Load FAISS indexes
    mood_index = faiss.read_index('movie_emotion_index.faiss')
    semantic_index = faiss.read_index('movie_semantic_index.faiss')
    tagline_index = faiss.read_index('movie_tagline_index.faiss')
    # Perform FAISS similarity search
    mood_distances, mood_indices = mood_index.search(user_mood_embedding, top_k * 2)
    semantic_distances, semantic_indices = semantic_index.search(user_semantic_embedding, top_k * 2)
    tagline_distances, tagline_indices = tagline_index.search(user_tagline_embedding, top_k * 2)
    # Combine and score results
    combined_scores = {}
    for i, index in enumerate(mood_indices[0]):
        #mood_similarity = 1 / (1 + mood_distances[0][i])
        mood_similarity = mood_distances[0][i]
        combined_scores[index] = combined_scores.get(index, 0) + weight_mood * mood_similarity

    for i, index in enumerate(semantic_indices[0]):
        #semantic_similarity = 1 / (1 + semantic_distances[0][i])
        semantic_similarity = semantic_distances[0][i]
        combined_scores[index] = combined_scores.get(index, 0) + weight_semantic * semantic_similarity

    for i, index in enumerate(tagline_indices[0]):
        #mood_similarity = 1 / (1 + mood_distances[0][i])
        tagline_similarity = tagline_distances[0][i]
        combined_scores[index] = combined_scores.get(index, 0) + weight_tagline * tagline_similarity
    # Rank and retrieve top movies
    ranked_movies = sorted(combined_scores.items(), key=lambda item: item[1], reverse=True)
    recommendations = []

    for index, score in ranked_movies[:100]:
        metadata = movie_metadata.get(index)
        if metadata:
            recommendations.append({
                "title": metadata["title"],
                "popularity": metadata["popularity"],
                "runtime": metadata["runtime"],
                'genres': metadata["genres"],
                "original_language": metadata["original_language"],
                "score": score,
            })

    return pd.DataFrame(recommendations)