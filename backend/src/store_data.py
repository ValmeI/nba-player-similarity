from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from backend.utils.app_logger import logger
from backend.src.player_stats_to_embeddings import create_season_embeddings
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

    def upsert_player_data_to_qdrant(self, processed_df: pd.DataFrame):

        logger.info(f"Upserting player embeddings and metadata to the Qdrant collection '{self.collection_name}'...")
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

            self.client.upsert(
                collection_name=self.collection_name,
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

    def store_player_embedding(
        self,
        player_stats_df: pd.DataFrame,
    ):

        player_name = player_stats_df.iloc[0]["PLAYER_NAME"]
        logger.info(f"Processing player '{player_name}' for embeddings and metadata...")
        processed_df = create_season_embeddings(player_stats_df)

        # initialize_qdrant_collection(client, collection_name, len(processed_df.iloc[0]["embeddings"]), reset_collection)
        self.upsert_player_data_to_qdrant(processed_df)

        logger.info(f"Player '{player_name}' embeddings and metadata stored in Qdrant.")

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
                    logger.info(f"Successfully processed file: {file_path}")
                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {e}")

        logger.info("All player files processed and stored in Qdrant.")
