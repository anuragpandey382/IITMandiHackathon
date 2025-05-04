## To be run from the root directory of the repo only
import os
import pandas as pd
import torch
from tqdm.auto import tqdm
from transformers import BertTokenizer, BertForSequenceClassification
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document


model_path = "./KnowledgeBase/" 
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
tokenizer = BertTokenizer.from_pretrained(model_path)
model = BertForSequenceClassification.from_pretrained(model_path).to(device)
model.eval()

emotion_list = [
    "admiration","amusement","anger","annoyance","approval","caring",
    "confusion","curiosity","desire","disappointment","disapproval",
    "disgust","embarrassment","excitement","fear","gratitude","grief",
    "joy","love","nervousness","optimism","pride","realization",
    "relief","remorse","sadness","surprise","neutral",
]

def predict_mood(text: str) -> str:
    """Return a comma-separated list of predicted emotions, or 'neutral'."""
    if not isinstance(text, str) or not text.strip():
        return "neutral"
    inputs = tokenizer(text, padding=True, truncation=True, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = model(**inputs)
    probs = torch.sigmoid(outputs.logits).cpu().numpy()[0]
    dic = []
    for i in range(len(probs)):
        dic.append((probs[i], emotion_list[i]))
    dic.sort(reverse=True)
    preds = [emotion_list[i] for i, p in enumerate(probs) if p > 0.3]
    return ", ".join([x[1] for x in dic[0:3]])


csv_file = "./KnowledgeBase/lang.csv"
df = pd.read_csv(csv_file)
tqdm.pandas(desc="Predicting moods")

df["mood"] = df["overview"].progress_apply(predict_mood)


df.to_csv(csv_file, index=False)
print("Added 'mood' column to CSV.")



embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
vector_store = Chroma(
    collection_name="Knowledge_Base_Movies_with_lang",
    embedding_function=embeddings,
    persist_directory="./kb_db",
)
docs = []
for _, row in tqdm(df.iterrows(), total=len(df), desc="Preparing documents"):
    content = (
        f"Movie Name: {row['original_title']}\n"
        f"Language: {row['original_language']}\n"
        f"Genre: {row['genres']}\n"
        f"Director: {row['director']}\n"
        f"Cast: {row['cast']}\n"
        f"Release Date: {row['release_date']}\n"
        f"Runtime: {row['runtime']} minutes\n"
        f"Mood: {row['mood']}\n"
        f"Overview: {row['overview']}\n"
    )
    metadata = {
        'original_language': row['original_language'],
        'genres': row['genres'],
        'original_title': row['original_title'],
        'director': row['director'],
        'cast': row['cast'],
        'release_date': row['release_date'],
        'runtime': row['runtime'],
        'vote_count': row.get('vote_count'),
        'revenue': row.get('revenue'),
        'mood': row['mood'],
    }
    docs.append(Document(page_content=content, metadata=metadata))


vector_store.add_documents(documents=docs)
print("✅ All documents added to Chroma vector store.")
