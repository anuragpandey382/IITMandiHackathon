import os
import torch
import pickle
from langchain.document_loaders import PyMuPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma

# Step 1: Load all PDFs and TXT files from input directory
pdf_dir = "data/DatasetMatlab"
all_docs = []

for file in os.listdir(pdf_dir):
    full_path = os.path.join(pdf_dir, file)

    if file.endswith(".pdf"):
        loader = PyMuPDFLoader(full_path)
    elif file.endswith(".txt"):
        loader = TextLoader(full_path, encoding="utf-8")
    else:
        continue  # Skip unsupported files

    docs = loader.load()
    if not docs:
        print(f"⚠️ No text extracted from: {file}")
    else:
        print(f"✅ Extracted {len(docs)} document(s) from {file}")

    for doc in docs:
        doc.metadata["source"] = file  # Add filename as metadata
    all_docs.extend(docs)

print(f"✅ Loaded {len(all_docs)} total documents from {len(os.listdir(pdf_dir))} files.")

# Step 2: Split documents into chunks
splitter = RecursiveCharacterTextSplitter(chunk_size=1024, chunk_overlap=192)
chunks = splitter.split_documents(all_docs)

print(f"✅ Split into {len(chunks)} total chunks.")

# Step 3: Set up HuggingFace embedding model (BGE base)
embedding_model = HuggingFaceEmbeddings(
    model_name="BAAI/bge-base-en-v1.5",
    model_kwargs={"device": "cuda" if torch.cuda.is_available() else "cpu"}
)

# Step 4: Create Chroma vectorstore and persist it
persist_dir = "output/chroma_index"
vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embedding_model,
    persist_directory=persist_dir
)
vectorstore.persist()

print(f"✅ Embeddings saved to Chroma DB at: {persist_dir}")

# Step 5 (Optional): Save text and metadata separately for later reference
os.makedirs("output", exist_ok=True)
with open("output/chunks.pkl", "wb") as f:
    pickle.dump([chunk.page_content for chunk in chunks], f)
with open("output/metadata.pkl", "wb") as f:
    pickle.dump([chunk.metadata for chunk in chunks], f)

print("✅ Chunk data and metadata saved.")
