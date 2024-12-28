import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from backend.utils.app_logger import logger
from backend.src.player_stats_to_embeddings import create_player_embeddings
from backend.config import settings
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm


class QdrantClientWrapper:
    def __init__(self, host: str, port: int, collection_name: str):
        self.host = host
        self.port = port
        self.client = QdrantClient(host=self.host, port=self.port)
        self.collection_name = collection_name

    def initialize_qdrant_collection(self, vector_size: int, reset_collection: bool):

        existing_collections = [c.name for c in self.client.get_collections().collections]
        logger.info(f"Found existing collections: {existing_collections}")

        if self.collection_name in existing_collections:
            if reset_collection:
                logger.info(f"Resetting collection '{self.collection_name}'...")
                self.client.delete_collection(self.collection_name)
            else:
                logger.info(f"Collection '{self.collection_name}' already exists. Skipping reset.")
                return

        logger.info(f"Creating collection: '{self.collection_name}'...")
        self.client.create_collection(
            self.collection_name,
            vectors_config={
                "size": vector_size,
                "distance": settings.VECTOR_DISTANCE_METRIC,
            },
        )

    def upsert_players_data_to_qdrant(self, all_players_df: pd.DataFrame):
       
        for _, row in all_players_df.iterrows():
            # Convert metadata values to native Python types to avoid error "Unable to serialize unknown type: <class 'numpy.int64'>"
            metadata = {
                "PLAYER_NAME": str(row["PLAYER_NAME"]),
                "PTS_PER_GAME": float(row["PTS_PER_GAME"]),
                "REB_PER_GAME": float(row["REB_PER_GAME"]),
                "AST_PER_GAME": float(row["AST_PER_GAME"]),
                "STL_PER_GAME": float(row["STL_PER_GAME"]),
                "BLK_PER_GAME": float(row["BLK_PER_GAME"]),
                "TOV_PER_GAME": float(row["TOV_PER_GAME"]),
                "MIN_PER_GAME": float(row["MIN_PER_GAME"]),
                "TS%": float(row["TS%"]),
                "EFG%": float(row["EFG%"]),
                "FG%": float(row["FG%"]),
                "FT%": float(row["FT%"]),
                "PER": float(row["PER"]),
                "WS/48": float(row["WS/48"]),
                "USG%": float(row["USG%"]),
                "PTS_PER_36": float(row["PTS_PER_36"]),
                "AST_TO_RATIO": float(row["AST_TO_RATIO"]),
                "STL%": float(row["STL%"]),
                "BLK%": float(row["BLK%"]),
                "PTS_RESPONSIBILITY": float(row["PTS_RESPONSIBILITY"]),
            }

            logger.debug(
                f"Upserting player {row['PLAYER_NAME']} with PLAYER_ID: {row['PLAYER_ID']} as PLAYER_ID type: {type(row['PLAYER_ID'])} and metadata: {metadata}"
            )

            self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    PointStruct(
                        id=str(uuid.uuid4()),
                        vector=row["embeddings"],
                        payload=metadata,
                    )
                ],
            )
            logger.info(
                f"Upserted player {row['PLAYER_NAME']} embedding and metadata with PLAYER_ID: {row['PLAYER_ID']} to Qdrant."
            )

    def store_player_embedding(
        self,
        player_stats_df: pd.DataFrame,
    ):

        player_name = player_stats_df.iloc[0]["PLAYER_NAME"]
        logger.debug(f"Processing player '{player_name}' for embeddings and metadata...")
        processed_df = create_player_embeddings(player_stats_df)
        self.upsert_players_data_to_qdrant(processed_df)

    def _process_player_file(self, file_path: str):
        """
        Process a single player's file and store embeddings in Qdrant.
        """
        player_stats_df = pd.read_parquet(file_path)
        if player_stats_df.empty:
            logger.warning(f"Empty DataFrame for {file_path}")
            return
        self.store_player_embedding(player_stats_df=player_stats_df)

    def process_player_files_in_threads(
        self,
        file_paths: list,
        max_workers=10,
    ):

        if len(file_paths) == 0:
            logger.error("No player files found.")
            return

        logger.info("Starting processing of player files...")
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {
                executor.submit(self._process_player_file, file_path): file_path for file_path in file_paths
            }

            for future in tqdm(
                as_completed(future_to_file),
                total=len(future_to_file),
                desc="Storing Players into Qdrant",
                unit="player",
            ):
                file_path = future_to_file[future]
                try:
                    future.result()
                    logger.debug(f"Successfully processed file: {file_path}")
                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {e}")

        logger.info("All player files processed and stored in Qdrant.")
