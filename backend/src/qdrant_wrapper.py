from datetime import datetime
import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from backend.utils.app_logger import logger
from backend.src.embeddings import PlayerEmbeddings
from backend.config import settings
import pandas as pd
from tqdm import tqdm
from pprint import pformat
from data.process_data import fetch_all_players_from_local_files


class QdrantClientWrapper:
    def __init__(self, host: str, port: int, collection_name: str):
        self.host = host
        self.port = port
        self.client = QdrantClient(host=self.host, port=self.port)
        self.collection_name = collection_name

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()

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
                "distance": settings.QDRANT_VECTOR_DISTANCE_METRIC,
            },
        )

    def upsert_players_data_to_qdrant(self, all_players_df: pd.DataFrame):

        for _, row in tqdm(all_players_df.iterrows(), desc="Upserting players to Qdrant"):
            # Convert metadata values to native Python types to avoid error
            # "Unable to serialize unknown type: <class 'numpy.int64'>"
            metadata = {
                "PLAYER_NAME": str(row["PLAYER_NAME"]),
                "PLAYER_NAME_LOWER_CASE": str(row["PLAYER_NAME"]).lower(),
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
                "GP": int(row["GP"]),
                "GS": int(row["GS"]),
                "LAST_PLAYED_AGE": int(row["LAST_PLAYED_AGE"]),
                "LAST_PLAYED_SEASON": str(row["LAST_PLAYED_SEASON"]),
                "TOTAL_SEASONS": int(row["TOTAL_SEASONS"]),
                "CREATED_AT": datetime.now().isoformat(),
            }

            # Mainly added for debugging purposes
            normalized_metadata = {
                "NORMALIZED_PTS_PER_GAME": float(row["NORM_PTS_PER_GAME"]),
                "NORMALIZED_REB_PER_GAME": float(row["NORM_REB_PER_GAME"]),
                "NORMALIZED_AST_PER_GAME": float(row["NORM_AST_PER_GAME"]),
                "NORMALIZED_STL_PER_GAME": float(row["NORM_STL_PER_GAME"]),
                "NORMALIZED_BLK_PER_GAME": float(row["NORM_BLK_PER_GAME"]),
                "NORMALIZED_TOV_PER_GAME": float(row["NORM_TOV_PER_GAME"]),
                "NORMALIZED_MIN_PER_GAME": float(row["NORM_MIN_PER_GAME"]),
                "NORMALIZED_TS%": float(row["NORM_TS%"]),
                "NORMALIZED_EFG%": float(row["NORM_EFG%"]),
                "NORMALIZED_FG%": float(row["NORM_FG%"]),
                "NORMALIZED_FT%": float(row["NORM_FT%"]),
                "NORMALIZED_PER": float(row["NORM_PER"]),
                "NORMALIZED_WS/48": float(row["NORM_WS/48"]),
                "NORMALIZED_USG%": float(row["NORM_USG%"]),
                "NORMALIZED_PTS_PER_36": float(row["NORM_PTS_PER_36"]),
                "NORMALIZED_AST_TO_RATIO": float(row["NORM_AST_TO_RATIO"]),
                "NORMALIZED_STL%": float(row["NORM_STL%"]),
                "NORMALIZED_BLK%": float(row["NORM_BLK%"]),
                "NORMALIZED_PTS_RESPONSIBILITY": float(row["NORM_PTS_RESPONSIBILITY"]),
                "NORMALIZED_GP": float(row["NORM_GP"]),
                "NORMALIZED_GS": float(row["NORM_GS"]),
                "NORMALIZED_LAST_PLAYED_AGE": float(row["NORM_LAST_PLAYED_AGE"]),
                "NORMALIZED_TOTAL_SEASONS": float(row["NORM_TOTAL_SEASONS"]),
                "EMBEDDINGS": str(row["embeddings"]),
            }

            logger.debug(
                f"Upserting player {row['PLAYER_NAME']} with PLAYER_ID: {row['PLAYER_ID']} as PLAYER_ID type: {type(row['PLAYER_ID'])} and metadata: {metadata} and normalized_metadata: {normalized_metadata}"
            )

            data_payload = {**metadata, **normalized_metadata}

            self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    PointStruct(
                        id=str(uuid.uuid4()),
                        vector=row["embeddings"],
                        payload=data_payload,
                    )
                ],
            )
        logger.info(f"Upserted {len(all_players_df)} players to Qdrant.")

    def store_players_embedding(
        self,
        data_dir: str,
    ):
        players_stats_df = fetch_all_players_from_local_files(data_dir)
        logger.debug(f"Processing players list of length {len(players_stats_df)} for embeddings and metadata...")
        embeddings_creator = PlayerEmbeddings(players_stats_df)
        processed_df = embeddings_creator.create_players_embeddings()
        self.upsert_players_data_to_qdrant(processed_df)

    def search_players_embeddings_by_name(self, player_name: str):
        player_name_lower = player_name.lower()
        logger.info(f"Searching for player {player_name} in Qdrant collection '{self.collection_name}'")
        results, _ = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter={"must": [{"key": "PLAYER_NAME_LOWER_CASE", "match": {"value": player_name_lower}}]},
            with_vectors=True,  # we need the vector to search for the player
            with_payload=True if settings.LOG_LEVEL == "DEBUG" else False,  # Fetch metadata payload only in debug mode
            limit=1,  # Only fetch one point
        )

        if results:
            logger.info(
                f"Found results: {len(results)} for player '{player_name}' in collection '{self.collection_name}'"
            )
            logger.debug(
                f"Found results for player '{player_name}' in collection '{self.collection_name}':\n{pformat(results[0].payload, indent=4)}"
            )
            embedding = results[0].vector
            return embedding
        else:
            raise ValueError(f"Player {player_name} not found in Qdrant.")

    def search_similar_players(self, query_vector: list):
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=settings.QDRANT_VECTOR_SEARCH_LIMIT,
            with_payload=True,
        )
        return results
