from neo4j import GraphDatabase
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
from typing import List, Union
import os
from pydantic import BaseModel, Field
from langchain_chroma import Chroma
import json
from langchain_huggingface import HuggingFaceEmbeddings
import numpy as np

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")

def Get_knowledge_Base_Lang():
    vector_store = Chroma(
        collection_name="Knowledge_Base_Movies_with_lang",
        embedding_function=embeddings,
        persist_directory="./kb_db",  
    )
    return vector_store

class MovieOut(BaseModel):
    title: str = Field(..., description="Movie title")
    year: int = Field(..., description="Release year")
    genre: str = Field(..., description="Genre(s)")
    director: str = Field(..., description="Director")
    runtime: int = Field(..., description="Runtime in minutes")
    rating: float = Field(..., description="Movie rating")
    overview: str = Field(..., description="Plot summary of the movie")

class TopKMovies(BaseModel):
    recommendations: List[MovieOut]

class DomainMatch(BaseModel):
    cls: str = Field(..., description="The single best-matching class from the domain")
vs = Get_knowledge_Base_Lang()
MOODS = ["Happy", "Sad", "Thrilling", "Romantic", "Adventurous", "Dark", "Inspiring"]
GENRE_NAMES = ["Action","Adventure", "Fantasy","Science Fiction","Crime","Drama","Thriller","Animation","Family","Western","Comedy","Romance","Horror","Mystery","History","War","Music","Documentary","Foreign","TV","Movie",]
LANGUAGE_NAMES = [ "English", "Japanese", "French", "Chinese", "Spanish","German","Russian","Korean","Telugu", "Italian","Dutch", "Tamil","Swedish", "Thai","Danish","Unknown","Hungarian","Czech","Portuguese", "Icelandic","Turkish","Norwegian Bokmål","Afrikaans","Polish","Hebrew", "Arabic","Vietnamese","Kyrgyz","Indonesian","Romanian","Persian","Norwegian","Slovenian","Pashto","Greek","Hindi",]
uri = "neo4j+s://0d57704b.databases.neo4j.io"
driver = GraphDatabase.driver(uri, auth=("neo4j", "5yPsvhzqDCZYx2s08eS3GvGLPM33v32IaQp-jEG3CdM"))
class MoviePreferences(BaseModel):
    mood: str = Field(description="User's desired mood. Choose from: " + ", ".join(MOODS))
    runtime: Union[int, str] = Field(description="Maximum runtime in minutes or 'any'")
    director: str = Field(description="Preferred director or 'any'")
    rating: Union[float, str] = Field(description="Minimum rating or 'any'")
prompt_template = PromptTemplate.from_template("""
You are an intelligent movie assistant. Extract structured movie preferences from the following user message.
Message: "{user_input}"
Return a JSON object with the following fields:
- mood: One of {candidate_moods} or 'any'
- runtime: Desired maximum runtime in minutes, or 'any'
- director: Preferred director, or 'any'
- rating: Minimum rating (e.g., 8.0), or 'any'
""".strip())
llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest", temperature=0.7,google_api_key=os.environ["GEMINI_API_KEY"])
# llm = ChatGroq(
#     model="llama-3.1-8b-instant",
#     temperature=0,
#     max_tokens=None,
#     timeout=None,
#     max_retries=2,
# )

recommender_template = PromptTemplate.from_template("""
You are a top-notch movie recommender.

User Preferences (JSON):
{user_data}

Candidate Movies (JSON array):
{candidates}

From these, choose the best {k} movies that most closely match the user's preferences.
Return your answer *only* in this JSON format:

```json
{{
  "recommendations": [
    {{
      "title": "…",
      "year": 2020,
      "genre": "Drama, Thriller",
      "director": "Name",
      "runtime": 120,
      "rating": 8.3,
      "overview": Plot summary of the movie
    }}
    // up to {k} entries
  ]
}}
```  
""".strip())
def get_top_movies_by_language(language_name: str, k: int = 10, max_runtime: Union[int,None] = None) -> List[dict]:
    with driver.session() as session:
        base = """
        MATCH (l:Language {name: $language_name})-[:IN_LANGUAGE]->(m:Movie)
        WHERE m.vote_count IS NOT NULL
        """
        if max_runtime is not None:
            base += " AND m.runtime <= $max_runtime"
        base += """
        RETURN m.title AS title,
               m.year AS year,
               m.vote_count AS votes,
               m.runtime AS runtime,
               m.overview AS overview
        ORDER BY m.vote_count DESC
        LIMIT $limit
        """
        result = session.run(base,
                             language_name=language_name,
                             max_runtime=max_runtime,
                             limit=k)
        return [dict(record) for record in result]




def get_movies_by_mood(mood: str, k: int = 10, language: str = None) -> List[dict]:
    with driver.session() as session:
        if language:
            query = """
            MATCH (mo:Mood {name: $mood})-[:RECOMMENDS]->(m:Movie)
            MATCH (l:Language {name: $language})-[:IN_LANGUAGE]->(m)
            RETURN m.title AS title,
                   m.year AS year,
                   m.vote_count AS votes,
                   m.runtime AS runtime,
                   m.overview AS overview,
                   m.rating AS rating
            ORDER BY m.vote_count DESC
            LIMIT $limit
            """
            params = {"mood": mood, "language": language, "limit": k}
        else:
            query = """
            MATCH (mo:Mood {name: $mood})-[:RECOMMENDS]->(m:Movie)
            RETURN m.title AS title,
                   m.year AS year,
                   m.vote_count AS votes,
                   m.runtime AS runtime,
                   m.overview AS overview,
                   m.rating AS rating
            ORDER BY m.vote_count DESC
            LIMIT $limit
            """
            params = {"mood": mood, "limit": k}
        result = session.run(query, **params)
        movies = []
        for record in result:
            movies.append({
                "title":    record["title"],
                "year":     record["year"],
                "votes":    record["votes"],
                "runtime":  record["runtime"],
                "overview": record["overview"],
                "rating":   record["rating"],
            })
        return movies


def get_movies_by_director(director_name: str, k: int = 10, max_runtime: Union[int,None] = None) -> List[dict]:
    with driver.session() as session:
        base = """
        MATCH (d:Director {name: $director_name})-[:DIRECTED]->(m:Movie)
        WHERE m.vote_count IS NOT NULL
        """
        if max_runtime is not None:
            base += " AND m.runtime <= $max_runtime"
        base += """
        RETURN m.title AS title,
               m.year AS year,
               m.vote_count AS votes,
               m.runtime AS runtime,
               m.overview AS overview,
               m.rating AS rating
        ORDER BY m.vote_count DESC
        LIMIT $limit
        """
        result = session.run(base,
                             director_name=director_name,
                             max_runtime=max_runtime,
                             limit=k)
        return [dict(record) for record in result]

def get_movies_by_genre(genre_name: str, k: int = 10, max_runtime: Union[int,None] = None) -> List[dict]:
    with driver.session() as session:
        base = """
        MATCH (m:Movie)-[:HAS_GENRE]->(g:Genre {name: $genre_name})
        WHERE m.vote_count IS NOT NULL
        """
        if max_runtime is not None:
            base += " AND m.runtime <= $max_runtime"
        base += """
        RETURN m.title AS title,
               m.year AS year,
               m.vote_count AS votes,
               m.runtime AS runtime,
               m.overview AS overview,
               m.rating AS rating
        ORDER BY m.vote_count DESC, m.rating DESC
        LIMIT $limit
        """
        result = session.run(base,
                             genre_name=genre_name,
                             max_runtime=max_runtime,
                             limit=k)
        return [dict(record) for record in result]


def match_into_domain(inp: str, domain: list[str]) -> str:
    template = """
        You have a domain of possible classes: {domain_list}.
        A user gave the input: "{user_text}".
        Match the input to the single semantically closest class in the domain.
        Return the result *only* in this JSON format:
        ```
            json
            {{ "match": "CLASS_NAME" }}
        // where CLASS_NAME is exactly one of the domain entries.
        ``` 
    """.strip()
    match_prompt = PromptTemplate.from_template(template.strip())
    prompt = match_prompt.invoke({
        "domain_list": ", ".join(domain),
        "user_text": inp
    })
    structured = llm.with_structured_output(DomainMatch)
    response = structured.invoke(prompt)
    for line in response.cls.strip().splitlines():
        if line:
            return line.strip()
    return ""

# def match_into_domain(inp: str, domain: list[str]) -> str:
#     """
#     Embed each domain entry and the input, then return the domain string
#     whose embedding has highest cosine similarity with the input embedding.
#     """
#     # 1. Embed domain entries
#     domain_embs = embeddings.embed_documents(domain)  # List[List[float]]

#     # 2. Embed the input query
#     query_emb = embeddings.embed_query(inp)           # List[float]
#     # 3. Convert to numpy arrays
#     D = np.vstack(domain_embs)   # shape (n_domain, dim)
#     q = np.array(query_emb)      # shape (dim,)
#     # 4. Normalize for cosine similarity
#     D_norm = D / np.linalg.norm(D, axis=1, keepdims=True)
#     q_norm = q / np.linalg.norm(q)
#     # 5. Compute cosine similarities and pick best
#     sims = D_norm.dot(q_norm)    # shape (n_domain,)
#     best_idx = int(np.argmax(sims))
#     return domain[best_idx]
def handle_Director(director, runtime, k):
    if(director):
        direc = get_movies_by_director(director, int(k),runtime )
        return director
    else:
        return []

def handle_Mood(mood, language, k):
    if(mood):
        mud = get_movies_by_mood(mood,k, language )
        return mud
    else:return []

def handle_Genre(genre, runtime, k):
    if(genre):
        genre = match_into_domain(genre, GENRE_NAMES)
        gen = get_movies_by_genre(genre, int(k), runtime)
        return gen
    else:
        return []
    
def handle_language(lang, runtime, k):
    if(lang):
        lg = match_into_domain(lang, LANGUAGE_NAMES)
        lg = get_top_movies_by_language(lang, int(k),runtime)
        return lg
    else:
        return []

def fetch_data_from_KG(user_data, k):
    prompt = []
    if(user_data.get("language", None)):
        language_movies = handle_language(user_data.get("language", None), user_data.get("runtime", None), k)
        prompt.extend(language_movies)
    if(user_data.get("genre",None)):
        genre_movies  = handle_Genre(user_data.get("genre",None), user_data.get("runtime", None), k)
        prompt.extend(genre_movies)
    if(user_data.get("director",None)):
        direc_movies = handle_Director(user_data.get("director",None),user_data.get("runtime",None), k)
        prompt.extend(direc_movies)
    if(user_data.get("mood",None)):
        direc_movies = handle_Mood(user_data.get("mood",None),user_data.get("language",None), k)
        prompt.extend(direc_movies)
    proprompt = recommender_template.invoke({
        "user_data":user_data,
        "candidates":prompt,
        "k":k
    })
    structured = llm.with_structured_output(TopKMovies)
    resp = structured.invoke(proprompt)
    result = []
    for rec in resp.recommendations:
        query = (
            f"{rec.title} ({rec.year}), genre: {rec.genre}, "
            f"directed by {rec.director}, {rec.runtime}min, rating {rec.rating}"
            f"overview {rec.overview}"
        )
        result.append(query)
    return result
def get_movie_from_recon(recommendations:List[MovieOut]):
    docs = []
    for rec in recommendations:
        query = (
            f"{rec.title} ({rec.year}), genre: {rec.genre}, "
            f"directed by {rec.director}, {rec.runtime}min, rating {rec.rating}"
            f"overview {rec.overview}"
        )
        results = vs.similarity_search(query, k=2)
        if results:
            docs.extend(results)
    print("Docs from KG", docs)
    return docs


if __name__=="__main__":
    spec = {"mood":"Dark","runtime":"120","director":"","genre":"Sci-Fi","language":"Hindi"}
    # print(get_movies_by_genre("Happy", 5, 350))
    print(fetch_data_from_KG(spec, 5))
    from neo4j._sync.driver import Driver as _Neo4jDriver
    def _noop_del(self):
        return None
    # override the finalizer so it never runs the broken code
    _Neo4jDriver.__del__ = _noop_del