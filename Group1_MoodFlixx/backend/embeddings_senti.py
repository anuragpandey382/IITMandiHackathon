import csv
import json

import lancedb
import pandas as pd


# 1. Load the movie embeddings from JSON
def load_embeddings(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        embeddings_dict = json.load(f)
    return embeddings_dict


# 2. Load selective metadata from CSV
def load_metadata(csv_file, columns_to_include):
    """
    Load only specified columns from the metadata CSV

    Args:
        csv_file: Path to the CSV file
        columns_to_include: List of column names to include from the CSV

    Returns:
        Dictionary mapping movie names to their metadata
    """
    metadata = {}

    with open(csv_file, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        # Check if movie_name is in the CSV
        if 'movie_name' not in reader.fieldnames:
            raise ValueError("CSV must contain a 'movie_name' column")

        # Validate columns_to_include against available columns
        valid_columns = [col for col in columns_to_include if col in reader.fieldnames]
        if len(valid_columns) < len(columns_to_include):
            missing = set(columns_to_include) - set(valid_columns)
            print(f"Warning: Some requested columns not found in CSV: {missing}")

        for row in reader:
            movie_name = row.get('movie_name', '').strip()
            if movie_name:
                # Extract only the requested columns
                movie_metadata = {
                    col: row.get(col, '').strip() if isinstance(row.get(col, ''), str) else row.get(col, '')
                    for col in valid_columns
                }
                metadata[movie_name] = movie_metadata

    print(f"Loaded selective metadata ({', '.join(valid_columns)}) for {len(metadata)} movies")
    return metadata


# 3. Convert to DataFrame format for LanceDB with selective metadata
def prepare_dataframe(embeddings_dict, metadata_dict=None):
    data = []
    for movie_name, embedding in embeddings_dict.items():
        # Start with basic embedding data
        entry = {
            "id": movie_name,
            "vector": embedding,
            "movie_name": movie_name
        }

        # Add metadata if available for this movie
        if metadata_dict and movie_name in metadata_dict:
            entry.update(metadata_dict[movie_name])

        data.append(entry)
    return pd.DataFrame(data)


# 4. Initialize LanceDB and create table
def create_vector_db(df, db_path="movie_vector_db"):
    # Connect to a database (creates it if it doesn't exist)
    db = lancedb.connect(db_path)

    # Create or overwrite a table
    table = db.create_table("movies", data=df, mode="overwrite")

    # Create vector search index for faster queries
    table.create_index(
        vector_column_name="vector",
        index_type="IVF_PQ",
        metric="cosine",
        num_partitions=256,
        num_sub_vectors=96
    )

    return db, table


embeddings_dict = load_embeddings("content/movie_embeddings_2500.json")
print(f"Loaded embeddings for {len(embeddings_dict)} movies")

# Load SELECTIVE metadata (only the columns you want)
# Specify exactly which columns to include from data1.csv
columns_to_include = ['movie_id', 'year', 'language', 'cast', 'director', 'industry', 'runtime', 'rating']
# based on your needs
metadata_dict = load_metadata("content/IMDB-Full_Detail_2500.csv", columns_to_include)

# Prepare dataframe with combined data
df = prepare_dataframe(embeddings_dict, metadata_dict)
print(f"Created DataFrame with {len(df)} rows")
print(f"DataFrame columns: {', '.join(df.columns)}")

# Create vector database
db, table = create_vector_db(df)
print(f"Created LanceDB table: {table.name}")
