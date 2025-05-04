import pandas as pd
import tensorflow as tf
from ast import literal_eval
# Load CSV with pandas
# print(df.columns)

# # Split features and label
# labels = df.pop("Title")  # Replace "label" with your label column name
# df.drop(['Actors', 'Director', 'Revenue (Millions)'], axis=1, inplace=True)
# features = df

# # Create TensorFlow dataset
# dataset = tf.data.Dataset.from_tensor_slices((dict(features), labels))
# dataset = dataset.batch(32)

# # Optional: preview one batch
# for features_batch, labels_batch in dataset.take(1):
#     print(features_batch)
#     print(labels_batch)

def create_dataset():
    # Load CSV with pandas
    df = pd.read_csv("dataset/IMDB-Movie-Data.csv")
    df.drop(['Actors', 'Director', 'Revenue (Millions)', 'Rank', 'Votes'], axis=1, inplace=True)
    features=[]
    for index, row in df.iterrows():
        title=row['Title']
        genre = row['Genre']
        year = row['Year']
        runtime = row['Runtime (Minutes)']
        rating = row['Rating']
        metascore = row['Metascore']
        description=row['Description']
        new_gen=str(genre).split(",")
        for gen in new_gen:
            new_row = {
                'Title' : title,
                'Genre': gen,
                'Year': year,
                'Runtime': runtime,
                'Rating': rating,
                'Metascore': metascore,
                'Description':description
            }
            features.append(new_row)

    features = pd.DataFrame(features)
    dataset = tf.data.Dataset.from_tensor_slices(dict(features))
    
    return dataset

def change_dataframe():
    df = pd.read_csv("dataset/movies.csv")
    df['year'] = df['title'].str.extract(r'\((\d{4})\)')
    df['clean_title'] = df['title'].str.replace(r'\s*\(\d{4}\)', '', regex=True)
    df['genres'] = df['genres'].str.split('|')
    df_exploded = df.explode('genres')
    df_final = df_exploded[['movieId', 'clean_title', 'year', 'genres']]
    df_final.columns = ['ID', 'Title', 'Year', 'Genre']
    tuples = list(df_final.itertuples(index=False, name=None))

    return df_final

def create_mvp_dataset():
    # Load CSV with pandas
    df = pd.read_csv("dataset/movies_parsed.csv")

    df = df.dropna()
    df['Year'] = df['Year'].astype(int)
    df['Runtime'] = df['Runtime'].astype(float)
    df['Popularity'] = df['Popularity'].astype(float)
    df['Title'] = df['Title'].astype(str)
    df['Genre'] = df['Genre'].apply(literal_eval).apply(lambda x: x if isinstance(x, list) else [])
    df['Language'] = df['Language'].astype(str)
    df['Description'] = df['Description'].astype(str)

    features=[]
    for index, row in df.iterrows():
        title=row['Title']
        genre = row['Genre']
        year = row['Year']
        runtime = row['Runtime']
        popularity = row['Popularity']
        description=row['Description']
        language = row['Language']
        for gen in genre:
            new_row = {
                'Title' : title,
                'Genre': gen,
                'Year': year,
                'Runtime': runtime,
                'Popularity': popularity,
                'Language': language,
                'Description':description
            }
            features.append(new_row)

    features = pd.DataFrame(features)
    print(len(features))
    dataset = tf.data.Dataset.from_tensor_slices(dict(features))
    
    return dataset

check = create_mvp_dataset()

for row in check.take(1):
    print(row)