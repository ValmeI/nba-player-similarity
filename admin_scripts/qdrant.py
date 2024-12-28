from qdrant_client import QdrantClient
from backend.src.search_api import prepare_input_query_vector, search_player_trajectory
from backend.utils.app_logger import logger
from backend.src.store_data import QdrantClientWrapper
from backend.config import settings
import json


def delete_collection(collection_name: str, host: str = "localhost", port: int = 6333):
    client = QdrantClient(host=host, port=port)
    collections = [c.name for c in client.get_collections().collections]
    print("Existing collections:", collections)

    # Drop collections
    client.delete_collection(collection_name)
    print("Collections after deletion:", [c.name for c in client.get_collections().collections])


def fetch_all_collections(host: str = "localhost", port: int = 6333):
    client = QdrantClient(host=host, port=port)
    collections = [c.name for c in client.get_collections().collections]
    print("Existing collections:", collections)
    return collections


def search_collection(collection_name: str, query: str, host: str = "localhost", port: int = 6333):
    client = QdrantClient(host=host, port=port)
    query_vector = prepare_input_query_vector(query)
    logger.info(f"Query vector: {query_vector}")
    search_result = client.search(
        collection_name=collection_name,
        query_vector=query_vector,
        limit=settings.VECTOR_SEARCH_LIMIT,
        with_payload=True,
    )
    logger.info(f"Found results: {json.dumps([result.payload for result in search_result], indent=1)}")
    return search_result


if __name__ == "__main__":
    # delete_collection("player_career_trajectory")
    # fetch_all_collections()
    # search_collection("player_career_trajectory", "kobe bryant")
    # search_player_trajectory("kobe bryant")
    # search_player_trajectory("Charles Nash")
    #search_player_trajectory("Larry Sykes")
    file_paths = [
        "nba_data/processed_parquet_files/Kobe_Bryant_full_player_stats.parquet"
    ]
    qdrant_object = QdrantClientWrapper(
        host=settings.QDRANT_HOST, port=settings.QDRANT_PORT, collection_name=settings.COLLECTION_NAME
    )
    qdrant_object.process_player_files_in_threads(
        file_paths=file_paths,
        max_workers=settings.MAX_THREADING_WORKERS,
    )
        
    
