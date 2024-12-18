# FastAPI otsinguteenuse kood

from fastapi import FastAPI
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient

app = FastAPI()
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
client = QdrantClient(host="localhost", port=6333)


@app.post("/search/")
def search_transactions(query: str):
    vector = model.encode(query).tolist()
    search_result = client.search(collection_name="transactions", query_vector=vector, limit=5)
    return {"results": [hit.payload for hit in search_result]}
