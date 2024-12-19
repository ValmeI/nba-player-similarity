from fastapi import FastAPI
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from backend.config import settings
from backend.utils.app_logger import logger
import json


app = FastAPI()
model = SentenceTransformer(settings.SENTENCE_TRANSFORMER_MODEL)
client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)


@app.post("/search/")
def search_transactions(query: str):
    vector = model.encode(query).tolist()
    search_result = client.search(collection_name="transactions", query_vector=vector, limit=5)
    logger.info(f"Found results: {json.dumps([result.payload for result in search_result], indent=1)}")
    format_results = [
        {
            "date": result.payload["date"],
            "description": result.payload["description"],
            "amount": result.payload["amount"],
            "sender_receiver_name": result.payload["sender_receiver_name"],
            "score": result.score,
        }
        for result in search_result
    ]
    return format_results
