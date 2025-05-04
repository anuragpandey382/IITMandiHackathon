## This file is a helper file to load the dataset, and then pre-process and store it in a vector Store DB
## Steps:
##      1. First we load the data
##      2. Then we enhance the Movie Metadata
##      2. Then we iterate over it and push each of the information to the Vector Store (Knowledge Base)
##      3. Add another Model?
import pandas as pd
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
def Load_language_dataset_into_Chroma():
    try:
        csv_file_path = './KnowledgeBase/lang.csv' 
        df = pd.read_csv(csv_file_path)
        print("Data loaded successfully!")
        vector_store = Chroma(
            collection_name="Knowledge_Base_Movies_with_lang",
            embedding_function=embeddings,
            persist_directory="./kb_db",  
        )
        langchain_documents = []

        for index, row in df.iterrows():
            # Create a Document object for each row
            document = Document(
                page_content=(
                    f"Movie Name: {row['original_title']}\n" 
                    f"Language: {row['original_language']}\n"
                    f"Genre: {row['genres']}\n"
                    f"Director: {row['director']}\n"
                    f"Cast: {row['cast']}\n"
                    f"Release Date: {row['release_date']}\n"
                    f"Runtime: {row['runtime']} minutes\n"
                    f"Overview: {row['overview']}\n"
                    f"Mood:{row['mood']}\n"
                ),
                metadata={
                    'original_language': row['original_language'],
                    'genres': row['genres'],
                    'original_title': row['original_title'],
                    'director': row['director'],
                    'cast': row['cast'],
                    'release_date': row['release_date'],
                    'runtime': row['runtime'],
                    'vote_count': row.get('vote_count', None),
                    'revenue': row.get('revenue', None),
                    'overview': row['overview'],
                    'mood':row['mood']
                }
            )
            langchain_documents.append(document)
        vector_store.add_documents(documents=langchain_documents)
        print("Documents Successfully Loaded into Knowledge Base Vector Store")
    except FileNotFoundError:
        print(f"Error: The file '{csv_file_path}' was not found.")
    except Exception as e:
        print(f"An error occurred while loading the CSV file: {e}")
def Get_knowledge_Base_Lang():
    vector_store = Chroma(
        collection_name="Knowledge_Base_Movies_with_lang",
        embedding_function=embeddings,
        persist_directory="./kb_db",  
    )
    return vector_store
if __name__ == "__main__":
    Load_language_dataset_into_Chroma()
    # Load_movie_metadata_into_Chroma()
    # Load_movie_credits_into_Chroma()
    # Load_movie_keywords_into_Chroma()
    # Load_movie_ratings_into_Chroma()
    # Load_movie_reviews_into_Chroma()
    # Load_movie_recommendations_into_Chroma()
    

