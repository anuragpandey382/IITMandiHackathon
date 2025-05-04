## This will Give us the most similar movies to a given movie (with info)
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from KnowledgeBase.structure_data import Get_Knowledge_Base
from KG.KG_pipeline import get_movies_by_director_and_runtime, get_top_k_movies_by_rating
def get_similar_movies_with_KG(movie_data: dict, top_k: int = 5, lang: str = "E"):
    from langchain_core.documents import Document
    from langchain_core.embeddings import Embeddings
    vector_store = Get_Knowledge_Base(flag=lang)
    query_text = f"""Movie Name: {movie_data['title']}
        Year: {movie_data['year']}
        Genre: {movie_data.get('genre', '')}
        Overview: {movie_data['overview']}
        Director: {movie_data['director']}
        Cast: {movie_data.get('cast', '')}
        Runtime : {movie_data.get('runtime', '')}
        Rating : {movie_data['rating']}"""
    similar_docs = vector_store.similarity_search(query_text, k=top_k)
    vector_results = [{
        "title": doc.metadata.get("movie_name"),
        "year": doc.metadata.get("year"),
        "genre": doc.metadata.get("genre"),
        "director": doc.metadata.get("director"),
        "cast": doc.metadata.get("cast"),
    } for doc in similar_docs]
    # Same director filtering
    same_director_movies = get_movies_by_director_and_runtime(
        movie_data['director'],
        movie_data.get("runtime", 200), 
        top_k
    )
    return {
        "vector_similar": vector_results,
        "same_director": same_director_movies
    }

if __name__ == "__main__":
    movie_data = {
        "title": "Couples Retreat",
        "year": 2009,
        "genre": "Comedy",
        "overview": "A comedy centered around four couples who settle into a tropical-island resort for a vacation. "
                    "While one of the couples is there to work on the marriage, the others fail to realize that "
                    "participation in the resort's therapy sessions is not optional.",
        "director": "Peter Billingsley",
        "cast": "Vince Vaughn, Malin Akerman, Jon Favreau, Jason Bateman",
        "runtime": 113,
        "rating": 5.5
    }
    print(get_similar_movies_with_KG(movie_data, 5, "E"))
