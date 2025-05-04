import pandas as pd
from neo4j import GraphDatabase

# -------- Configuration --------
NEO4J_URI = "neo4j+s://fea8a723.databases.neo4j.io"  # e.g., neo4j+s://abc.databases.neo4j.io
USERNAME = "neo4j"
PASSWORD = "Qp3U5o9HjMkHPuLjj9M4vL91doNcq3Hj4fGFpZV7-XI"
CSV_PATH = "eng.csv"  # path to your dataset

# -------- Load CSV --------
df = pd.read_csv(CSV_PATH)
df.dropna(subset=["Director", "Title"], inplace=True)

# -------- Connect to Neo4j --------
driver = GraphDatabase.driver(NEO4J_URI, auth=(USERNAME, PASSWORD))

def create_graph(tx, title, year, runtime, director):
    tx.run("""
        MERGE (d:Director {name: $director})
        MERGE (m:Movie {title: $title, year: $year})
        SET m.runtime = $runtime
        MERGE (d)-[:DIRECTED]->(m)
    """, director=director, title=title, year=year, runtime=runtime)

# -------- Insert Data --------
with driver.session() as session:
    for _, row in df.iterrows():
        session.execute_write(
            create_graph,
            row['Title'],
            int(row['Year']),
            int(row['Runtime (Minutes)']),
            row['Director']
        )

driver.close()
print("Knowledge graph created successfully.")
