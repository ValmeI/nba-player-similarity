from qdrant_client import QdrantClient
from backend.src.qdrant_wrapper import QdrantClientWrapper
from backend.config import settings
from icecream import ic


def delete_collection(collection_name: str, host: str, port: int):
    client = QdrantClient(host=host, port=port)
    collections = [c.name for c in client.get_collections().collections]
    print("Existing collections:", collections)

    # Drop collections
    client.delete_collection(collection_name)
    print("Collections after deletion:", [c.name for c in client.get_collections().collections])


def fetch_all_collections(host: str, port: int):
    client = QdrantClient(host=host, port=port)
    collections = [c.name for c in client.get_collections().collections]
    print("Existing collections:", collections)
    return collections


def test_search_players_embeddings_by_name(player_name: str, collection_name: str):
    with QdrantClientWrapper(
        host=settings.QDRANT_HOST, port=settings.QDRANT_PORT, collection_name=collection_name
    ) as qdrant_object:
        results = qdrant_object.search_players_embeddings_by_name(player_name)
        ic(results)


if __name__ == "__main__":
    # delete_collection(settings.QDRANT_COLLECTION_NAME)
    # fetch_all_collections()
    # search_collection(settings.QDRANT_COLLECTION_NAME, "kobe bryant")
    # search_player_trajectory("kobe bryant")
    # search_player_trajectory("Charles Nash")
    # search_player_trajectory("Larry Sykes")
    # file_paths = ["nba_data/processed_parquet_files/Kobe_Bryant_full_player_stats.parquet"]
    test_search_players_embeddings_by_name("LeBron James", collection_name=settings.QDRANT_COLLECTION_NAME)
