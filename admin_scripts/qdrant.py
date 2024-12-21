from qdrant_client import QdrantClient
from backend.src.search_api import prepare_input_query_vector


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
    search_result = client.search(
        collection_name=collection_name, query_vector=query_vector, limit=5, with_payload=True
    )
    return search_result


if __name__ == "__main__":
    delete_collection("player_career_trajectory")
    # fetch_all_collections()
    # search_collection("player_career_trajectory", "lebron james")
