from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from backend.utils.app_logger import logger
from backend.src.player_stats_to_embeddings import create_season_embeddings
from backend.config import settings
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm


def initialize_qdrant_collection(client: QdrantClient, collection_name: str, vector_size: int, reset_collection: bool):
    """
    Initialize the Qdrant collection: create or reset it as needed.

    Args:
        client (QdrantClient): Qdrant client instance.
        collection_name (str): Qdrant collection name.
        vector_size (int): Size of the vector.
        reset_collection (bool): Whether to reset the collection if it already exists.
    """
    existing_collections = [c.name for c in client.get_collections().collections]
    logger.info(f"Found existing collections: {existing_collections}")

    if collection_name in existing_collections:
        if reset_collection:
            logger.info(f"Resetting collection '{collection_name}'...")
            client.delete_collection(collection_name)
        else:
            logger.info(f"Collection '{collection_name}' already exists. Skipping reset.")
            return

    logger.info(f"Creating collection: '{collection_name}'...")
    client.create_collection(
        collection_name,
        vectors_config={
            "size": vector_size,
            "distance": settings.VECTOR_DISTANCE_METRIC,
        },
    )


def upsert_player_data_to_qdrant(client: QdrantClient, collection_name: str, processed_df: pd.DataFrame):
    """
    Upsert player embeddings and metadata into Qdrant.

    Args:
        client (QdrantClient): Qdrant client instance.
        collection_name (str): Qdrant collection name.
        processed_df (pd.DataFrame): DataFrame containing player stats and embeddings.
    """
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
            "true_shooting_percentage": row.get("TS%", None),
            "player_efficiency_rating": row.get("PER", None),
        }

        if None in stats_to_include.values():
            logger.error(f"Player {row['PLAYER_NAME']} of season {row['SEASON_ID']} has incomplete data.")
            continue

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
        logger.info(f"Upserted player {row['PLAYER_NAME']} of season {row['SEASON_ID']} to the Qdrant collection.")


def store_player_embeddings_to_qdrant(
    client: QdrantClient,
    collection_name: str,
    player_stats_df: pd.DataFrame,
):
    """
    Process player stats, create embeddings, and store in Qdrant.

    Args:
        collection_name (str): Qdrant collection name.
        player_stats_df (pd.DataFrame): DataFrame containing player stats and embeddings.
        host (str): Qdrant server host, default "localhost".
        port (int): Qdrant server port, default 6333.
    """
    player_name = player_stats_df.iloc[0]["PLAYER_NAME"]
    logger.info(f"Processing player '{player_name}' for embeddings and metadata...")
    processed_df = create_season_embeddings(player_stats_df)

    # initialize_qdrant_collection(client, collection_name, len(processed_df.iloc[0]["embeddings"]), reset_collection)
    upsert_player_data_to_qdrant(client, collection_name, processed_df)

    logger.info(f"Player '{player_name}' embeddings and metadata stored in Qdrant.")


def process_player_file(client: QdrantClient, file_path: str, collection_name: str):
    """
    Process a single player's file and store embeddings in Qdrant.
    """
    player_stats_df = pd.read_parquet(file_path)
    if player_stats_df.empty:
        logger.warning(f"Empty DataFrame for {file_path}")
        return
    store_player_embeddings_to_qdrant(client=client, collection_name=collection_name, player_stats_df=player_stats_df)


def process_player_files_in_threads(
    client,
    file_paths,
    collection_name,
    max_workers=10,
):
    """
    Process multiple player files concurrently using threading.

    Args:
        file_paths (list): List of file paths to process.
        collection_name (str): Name of the Qdrant collection.
        max_workers (int): Maximum number of threads to use.
        host (str): Qdrant server host.
        port (int): Qdrant server port.
    """

    def worker(file_path):
        process_player_file(client=client, file_path=file_path, collection_name=collection_name)

    logger.info("Starting processing of player files...")
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {executor.submit(worker, file_path): file_path for file_path in file_paths}

        for future in tqdm(as_completed(future_to_file), total=len(future_to_file), desc="Storing Players into Qdrant", unit="player"):
            file_path = future_to_file[future]
            try:
                future.result()
                logger.info(f"Successfully processed file: {file_path}")
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")

    logger.info("All player files processed and stored in Qdrant.")
