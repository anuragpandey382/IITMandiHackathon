"""
Create a vector store from the preprocessed movie data.
This script reads the processed CSV file, generates brief summaries for each movie,
and stores them in a ChromaDB vector store for semantic search.
"""

import os
import pandas as pd
from typing import List, Dict, Any
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
import time

# Constants
PROCESSED_DATA_PATH = "data/processed/processed_movies.csv"
VECTOR_DB_PATH = "data/vectordb"
BATCH_SIZE = 100  # Process movies in batches to avoid memory issues

def load_processed_data(path: str = PROCESSED_DATA_PATH) -> pd.DataFrame:
    """
    Load the processed movie data from CSV.
    
    Args:
        path: Path to the processed CSV file
        
    Returns:
        DataFrame containing the processed movie data
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Processed data file not found at {path}. Please run data_preprocess.py first.")
    
    return pd.read_csv(path)

def generate_movie_summary(movie_data: Dict[str, Any]) -> str:
    """
    Generate a brief summary for a movie using its metadata.
    
    Args:
        movie_data: Dictionary containing movie metadata
        
    Returns:
        Brief summary of the movie
    """
    # Determine the mood of the movie based on genres and other metadata
    mood = determine_movie_mood(movie_data)
    
    # Create a summary template
    summary_template = """
    {title} ({year}) is a {genres} film directed by {director}.
    It stars {actors} and has an IMDB rating of {imdb_score}/10.
    The movie is {duration} minutes long and was produced in {country}.
    This film has a {mood} mood and atmosphere.
    {plot_summary}
    """
    
    # Format actor names
    actors = []
    for i in range(1, 4):
        actor_col = f'actor_{i}_name'
        if actor_col in movie_data and movie_data[actor_col] != 'Unknown':
            actors.append(movie_data[actor_col])
    
    actors_str = ", ".join(actors) if actors else "Unknown actors"
    
    # Format the summary
    summary = summary_template.format(
        title=movie_data.get('movie_title', 'Unknown'),
        year=movie_data.get('title_year', 'Unknown'),
        genres=movie_data.get('genres', 'Unknown'),
        director=movie_data.get('director_name', 'Unknown'),
        actors=actors_str,
        imdb_score=movie_data.get('imdb_score', 'Unknown'),
        duration=movie_data.get('duration', 'Unknown'),
        country=movie_data.get('country', 'Unknown'),
        mood=mood,
        plot_summary=movie_data.get('plot_summary', '')
    )
    
    return summary.strip()

def determine_movie_mood(movie_data: Dict[str, Any]) -> str:
    """
    Determine the mood of a movie based on its genres and other metadata.
    
    Args:
        movie_data: Dictionary containing movie metadata
        
    Returns:
        Mood description of the movie
    """
    # Get the genres and ensure they're strings
    genres = str(movie_data.get('genres', '')) if movie_data.get('genres') is not None else ''
    genres = genres.lower()
    
    # Get plot keywords and ensure they're strings
    plot_keywords = str(movie_data.get('plot_keywords', '')) if movie_data.get('plot_keywords') is not None else ''
    plot_keywords = plot_keywords.lower()
    
    # Define genre-to-mood mappings
    mood_mappings = {
        'comedy': ['lighthearted', 'humorous', 'cheerful', 'playful'],
        'romance': ['romantic', 'heartwarming', 'tender', 'emotional'],
        'horror': ['tense', 'frightening', 'suspenseful', 'eerie'],
        'thriller': ['suspenseful', 'intense', 'gripping', 'mysterious'],
        'action': ['exciting', 'adrenaline-pumping', 'dynamic', 'intense'],
        'drama': ['emotional', 'thought-provoking', 'serious', 'poignant'],
        'sci-fi': ['imaginative', 'futuristic', 'mind-bending', 'speculative'],
        'adventure': ['adventurous', 'thrilling', 'exciting', 'epic'],
        'fantasy': ['magical', 'whimsical', 'enchanting', 'imaginative'],
        'animation': ['colorful', 'imaginative', 'whimsical', 'playful'],
        'documentary': ['informative', 'thought-provoking', 'educational', 'revealing'],
        'crime': ['gritty', 'tense', 'suspenseful', 'dark'],
        'mystery': ['intriguing', 'puzzling', 'suspenseful', 'enigmatic'],
        'war': ['intense', 'dramatic', 'powerful', 'harrowing'],
        'western': ['rugged', 'gritty', 'adventurous', 'atmospheric'],
        'musical': ['uplifting', 'melodic', 'rhythmic', 'expressive'],
        'family': ['heartwarming', 'wholesome', 'uplifting', 'playful']
    }
    
    # Check for specific keywords that might indicate mood
    keyword_mood_mappings = {
        'dark': 'dark',
        'gritty': 'gritty',
        'uplifting': 'uplifting',
        'inspirational': 'inspirational',
        'melancholy': 'melancholy',
        'nostalgic': 'nostalgic',
        'atmospheric': 'atmospheric',
        'surreal': 'surreal',
        'tense': 'tense',
        'quirky': 'quirky',
        'heartwarming': 'heartwarming'
    }
    
    # Collect potential moods
    potential_moods = []
    
    # Check genres
    for genre, moods in mood_mappings.items():
        if genre in genres:
            potential_moods.extend(moods)
    
    # Check keywords
    for keyword, mood in keyword_mood_mappings.items():
        if keyword in plot_keywords:
            potential_moods.append(mood)
    
    # If we have potential moods, choose one or combine them
    if potential_moods:
        # If there are multiple moods, choose up to 2 different ones
        unique_moods = list(set(potential_moods))
        if len(unique_moods) >= 2:
            return f"{unique_moods[0]} and {unique_moods[1]}"
        elif len(unique_moods) == 1:
            return unique_moods[0]
    
    # Default mood based on IMDB score if no specific mood is determined
    try:
        imdb_score = float(movie_data.get('imdb_score', 0))
    except (ValueError, TypeError):
        imdb_score = 0
        
    if imdb_score >= 7.5:
        return "captivating and well-crafted"
    elif imdb_score >= 6.0:
        return "engaging"
    else:
        return "mixed"

def create_movie_documents(df: pd.DataFrame) -> List[Document]:
    """
    Create Document objects for each movie in the dataset.
    
    Args:
        df: DataFrame containing the processed movie data
        
    Returns:
        List of Document objects
    """
    documents = []
    
    # Process movies in batches to avoid memory issues
    total_movies = len(df)
    print(f"Creating document objects for {total_movies} movies...")
    
    for i in range(0, total_movies, BATCH_SIZE):
        batch = df.iloc[i:min(i+BATCH_SIZE, total_movies)]
        print(f"Processing batch {i//BATCH_SIZE + 1}/{(total_movies + BATCH_SIZE - 1)//BATCH_SIZE}...")
        
        for _, row in batch.iterrows():
            # Convert row to dictionary
            movie_data = row.to_dict()
            
            # Generate summary
            summary = generate_movie_summary(movie_data)
            
            # Create metadata for the document
            metadata = {
                "title": movie_data.get('movie_title', 'Unknown'),
                "year": int(movie_data.get('title_year', 0)),
                "director": movie_data.get('director_name', 'Unknown'),
                "actors": ", ".join([
                    movie_data.get('actor_1_name', 'Unknown'),
                    movie_data.get('actor_2_name', 'Unknown'),
                    movie_data.get('actor_3_name', 'Unknown')
                ]),
                "genres": ", ".join(movie_data.get('genres', '').split('|') if isinstance(movie_data.get('genres', ''), str) else []),
                "duration": int(movie_data.get('duration', 0)),
                "language": movie_data.get('language', 'Unknown'),
                "country": movie_data.get('country', 'Unknown'),
                "imdb_score": float(movie_data.get('imdb_score', 0.0)),
                "keywords": ", ".join(movie_data.get('plot_keywords', '').split('|') if isinstance(movie_data.get('plot_keywords', ''), str) else [])
            }
            
            # Create the document
            doc = Document(page_content=summary, metadata=metadata)
            documents.append(doc)
    
    return documents

def create_vector_store(documents: List[Document], path: str = VECTOR_DB_PATH) -> Chroma:
    """
    Create a vector store from the movie documents.
    
    Args:
        documents: List of Document objects
        path: Path to save the vector store to
        
    Returns:
        Chroma vector store
    """
    # Create the directory if it doesn't exist
    os.makedirs(path, exist_ok=True)
    
    print(f"Creating vector store at {path}...")
    
    # Manually filter complex metadata to ensure compatibility with ChromaDB
    filtered_documents = []
    for doc in documents:
        # Create a new metadata dictionary with only simple types
        filtered_metadata = {}
        for key, value in doc.metadata.items():
            # Only include simple types (str, int, float, bool)
            if isinstance(value, (str, int, float, bool)):
                filtered_metadata[key] = value
        
        # Create a new document with filtered metadata
        filtered_doc = Document(page_content=doc.page_content, metadata=filtered_metadata)
        filtered_documents.append(filtered_doc)
    
    # Initialize the embeddings model
    # Using a smaller, free model for efficiency
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    # Create the vector store
    vector_store = Chroma.from_documents(
        documents=filtered_documents,
        embedding=embeddings,
        persist_directory=path
    )
    
    # Persist the vector store
    vector_store.persist()
    print(f"Vector store created and persisted at {path}")
    
    return vector_store

def test_vector_store(vector_store: Chroma) -> None:
    """
    Test the vector store with some example queries.
    
    Args:
        vector_store: Chroma vector store to test
    """
    print("\nTesting vector store with example queries...")
    
    test_queries = [
        "Action movies with high IMDB ratings",
        "Romantic comedies from the 2000s",
        "Science fiction movies directed by Christopher Nolan",
        "Drama movies about family relationships",
        "Movies starring Tom Hanks with good reviews"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        results = vector_store.similarity_search(query, k=3)
        
        for i, doc in enumerate(results):
            print(f"\n  Result {i+1}: {doc.metadata['title']} ({doc.metadata['year']})")
            print(f"  Director: {doc.metadata['director']}")
            print(f"  Genres: {', '.join(doc.metadata['genres'])}")
            print(f"  IMDB Score: {doc.metadata['imdb_score']}")
            print(f"  Summary: {doc.page_content[:150]}...")

def main():
    """Main function to create the vector store."""
    try:
        # Load the processed data
        print("Loading processed movie data...")
        df = load_processed_data()
        print(f"Loaded {len(df)} movies from processed data.")
        
        # Create documents
        documents = create_movie_documents(df)
        print(f"Created {len(documents)} document objects.")
        
        # Create vector store
        vector_store = create_vector_store(documents)
        
        # Test the vector store
        test_vector_store(vector_store)
        
        print("\nVector store creation completed successfully!")
        
    except Exception as e:
        print(f"Error creating vector store: {str(e)}")

if __name__ == "__main__":
    main()