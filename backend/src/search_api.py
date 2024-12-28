from fastapi import FastAPI, HTTPException
from qdrant_client import QdrantClient
from backend.config import settings
from backend.utils.app_logger import logger
from backend.src.player_stats_to_embeddings import create_player_embeddings
from backend.utils.search_results import (
    remove_same_player,
    filter_search_result,
    format_logger_search_result,
    format_search_result,
)
from data.process_data import get_player_stats_from_local_file
import pandas as pd

app = FastAPI()
client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)


def prepare_input_query_vector(player_name: str) -> list:
    """
    Fetch user input player stast and prepare the query vector for similarity search.

    Args:
        player_name (str): Name of the input player.

    Returns:
        list: Query vector representing the player's career trajectory.
    """
    try:
        player_stats_df = get_player_stats_from_local_file(player_name, settings.PROCESSED_NBA_DATA_PATH)
        logger.debug(f"Player stats for {player_name}: \n{player_stats_df}")
        processed_df = create_player_embeddings(player_stats_df)
        logger.debug(f"Embedded player stats for {player_name}: \n{processed_df}")
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    query_vector = processed_df["embeddings"].apply(pd.Series).median(axis=0).tolist()
    logger.debug(f"Query vector for {player_name}: {query_vector}")
    return query_vector


@app.post("/search/")
def search_player_trajectory(player_name: str):
    player_name = player_name.lower()
    logger.info(f'Received search query for player: "{player_name}"')

    query_vector = prepare_input_query_vector(player_name)

    search_result = client.search(
        collection_name="player_career_trajectory",
        query_vector=query_vector,
        limit=settings.VECTOR_SEARCH_LIMIT,
        with_payload=True,
    )

    # search_result = remove_same_player(search_result, player_name)
    # search_result = filter_search_result(search_result, settings.VECTOR_SEARCH_SCORE_THRESHOLD)

    logger.info(f"Found results: {format_logger_search_result(search_result)}")
    return format_search_result(search_result)
