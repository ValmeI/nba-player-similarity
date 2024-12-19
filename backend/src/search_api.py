# FastAPI otsinguteenuse kood

from fastapi import FastAPI
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from backend.config import settings

app = FastAPI()
model = SentenceTransformer(settings.SENTENCE_TRANSFORMER_MODEL)
client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)


@app.post("/search/")
def search_transactions(query: str):
    vector = model.encode(query).tolist()
    search_result = client.search(collection_name="transactions", query_vector=vector, limit=5)
    return {"results": [hit.payload for hit in search_result]}
