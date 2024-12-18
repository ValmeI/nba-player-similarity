from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from backend.utils.app_logger import logger
from backend.src.process_data import load_and_process_csv


def store_embeddings_to_qdrant(collection_name: str, data_path: str, host: str = "localhost", port: int = 6333):
    """
    Function to store embeddings and metadata to Qdrant

    Args:
        collection_name (str): Qdranti collection name.
        data_path (str): CSV file path.
        host (str): Qdranti server host, default "localhost".
        port (int): Qdranti server port, default 6333.
    """

    logger.info("Load and process CSV...")
    df = load_and_process_csv(data_path)
    client = QdrantClient(host=host, port=port)

    if collection_name not in [c.name for c in client.get_collections().collections]:
        logger.info(f"Creating collection if not exists: '{collection_name}'...")
        client.create_collection(collection_name, vectors_config={"size": 384, "distance": "Cosine"})

    logger.info(f"Saving embeddings and metadata to the Qdrant collection '{collection_name}'...")
    for idx, row in df.iterrows():
        client.upsert(
            collection_name=collection_name,
            points=[
                PointStruct(
                    id=idx,
                    vector=row["embeddings"],
                    payload={
                        "description": row["Description"],
                        "amount": row["Amount"],
                        "date": row["Date"],
                        "name": row["Sender/receiver name"],
                    },
                )
            ],
        )

    logger.info("Embeddings and metadata saved to the Qdrant collection.")
