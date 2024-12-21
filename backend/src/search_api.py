from fastapi import FastAPI, HTTPException
from qdrant_client import QdrantClient
from backend.config import settings
from backend.utils.app_logger import logger
from backend.src.process_data import create_season_embeddings
from backend.utils.search_results import remove_duplicates, remove_same_player
from data.get_nba_data import get_player_stats_from_local_file
import json
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
        player_stats_df = get_player_stats_from_local_file(player_name)
        logger.debug(f"Player stats for {player_name}: \n{player_stats_df}")
        processed_df = create_season_embeddings(player_stats_df)
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

    # logger.info(f"Removing duplicate results for player: {player_name}")
    # search_result = remove_duplicates(search_result) # TODO. see if needed

    search_result = remove_same_player(search_result, player_name)
    logger.info(f"Found results: {json.dumps([result.payload for result in search_result], indent=1)}")
    formatted_results = [
        {
            "player_name": result.payload["player_name"],
            "season_id": result.payload["season_id"],
            "points_per_game": result.payload.get("points_per_game"),
            "offensive_rebounds_per_game": result.payload.get("offensive_rebounds_per_game"),
            "defensive_rebounds_per_game": result.payload.get("defensive_rebounds_per_game"),
            "steals_per_game": result.payload.get("steals_per_game"),
            "assists_per_game": result.payload.get("assists_per_game"),
            "blocks_per_game": result.payload.get("blocks_per_game"),
            "turnovers_per_game": result.payload.get("turnovers_per_game"),
            "personal_fouls_per_game": result.payload.get("personal_fouls_per_game"),
            "similarity_score": result.score,
        }
        for result in search_result
    ]

    return formatted_results
