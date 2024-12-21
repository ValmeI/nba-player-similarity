from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from backend.utils.app_logger import logger
from backend.src.process_data import create_season_embeddings
from backend.config import settings
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import os


def store_player_embeddings_to_qdrant(
    collection_name: str,
    player_stats_df: pd.DataFrame,
    host: str = "localhost",
    port: int = 6333,
    reset_collection: bool = False,
):
    """
    Function to store player embeddings and metadata to Qdrant.

    Args:
        collection_name (str): Qdrant collection name.
        player_stats_df (pd.DataFrame): DataFrame containing player stats and embeddings.
        host (str): Qdrant server host, default "localhost".
        port (int): Qdrant server port, default 6333.
        reset_collection (bool): Whether to reset the collection if it already exists.
    """
    logger.info("Processing player stats and creating embeddings...")
    processed_df = create_season_embeddings(player_stats_df)
    client = QdrantClient(host=host, port=port)

    existing_collections = [c.name for c in client.get_collections().collections]
    logger.info(f"Found existing collections: {existing_collections}")

    if collection_name in existing_collections:
        if reset_collection:
            logger.info(f"Resetting collection '{collection_name}'...")
            client.delete_collection(collection_name)
            client.create_collection(
                collection_name,
                vectors_config={
                    "size": len(processed_df.iloc[0]["embeddings"]),
                    "distance": settings.VECTOR_DISTANCE_METRIC,
                },
            )
        else:
            logger.info(f"Collection '{collection_name}' already exists. Skipping reset.")
    else:
        logger.info(f"Creating collection: '{collection_name}'...")
        client.create_collection(
            collection_name,
            vectors_config={
                "size": len(processed_df.iloc[0]["embeddings"]),
                "distance": settings.VECTOR_DISTANCE_METRIC,
            },
        )

    logger.info(f"Upserting player embeddings and metadata to the Qdrant collection '{collection_name}'...")
    for idx, row in processed_df.iterrows():

        stats_to_include = {
            "points_per_game": row.get("PTS_PER_GAME", None),
            "offensive_rebounds_per_game": row.get("OREB_PER_GAME", None),
            "defensive_rebounds_per_game": row.get("DREB_PER_GAME", None),
            "steals_per_game": row.get("STL_PER_GAME", None),
            "assists_per_game": row.get("AST_PER_GAME", None),
            "blocks_per_game": row.get("BLK_PER_GAME", None),
            "turnovers_per_game": row.get("TOV_PER_GAME", None),
            "personal_fouls_per_game": row.get("PF_PER_GAME", None),
        }

        client.upsert(
            collection_name=collection_name,
            points=[
                PointStruct(
                    id=idx,
                    vector=row["embeddings"],
                    payload={
                        "season_id": row["SEASON_ID"],
                        "player_name": row["PLAYER_NAME"],
                        **stats_to_include,
                    },
                )
            ],
        )

    logger.info("Player embeddings and metadata saved to the Qdrant collection.")


def process_player_file(file_path, collection_name, host="localhost", port=6333, reset_collection=False):
    """
    Process a single player's file and store embeddings in Qdrant.
    """
    player_stats_df = pd.read_parquet(file_path)
    store_player_embeddings_to_qdrant(
        collection_name=collection_name,
        player_stats_df=player_stats_df,
        host=host,
        port=port,
        reset_collection=reset_collection,
    )


def process_player_files_in_threads(
    file_paths, collection_name, max_workers=10, host="localhost", port=6333, reset_collection=False
):
    """
    Process multiple player files concurrently using threading.

    Args:
        file_paths (list): List of file paths to process.
        collection_name (str): Name of the Qdrant collection.
        max_workers (int): Maximum number of threads to use.
        host (str): Qdrant server host.
        port (int): Qdrant server port.
        reset_collection (bool): Whether to reset the Qdrant collection.
    """

    def worker(file_path):
        process_player_file(file_path, collection_name, host, port, reset_collection)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        executor.map(worker, file_paths)


if __name__ == "__main__":
    folder_path = "data/players_parquet"
    logger.info(f"Loading data from {folder_path}")
    load_file_paths = os.listdir(folder_path)
    logger.info(f"Found {len(load_file_paths)} files")
    process_player_files_in_threads(
        file_paths=load_file_paths,
        collection_name="player_career_trajectory",
        max_workers=10,
        host="localhost",
        port=6333,
        reset_collection=False,
    )
