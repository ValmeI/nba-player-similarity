import asyncio
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from shared.config import settings
from backend.src.qdrant_wrapper import AsyncQdrantClientWrapper
from backend.src.recent_searches_store import recent_searches_store
from shared.utils.app_logger import logger
from backend.utils.search_results import (
    format_logger_search_result,
    remove_same_player,
    format_similar_players_search_result,
    format_user_requested_player_career_stats,
)
from backend.src.player_real_name import get_real_player_name

app = FastAPI()
client = AsyncQdrantClientWrapper(
    host=settings.QDRANT_HOST, port=settings.QDRANT_PORT, collection_name=settings.QDRANT_COLLECTION_NAME
)


@app.get("/")
async def get_root() -> dict[str, str]:
    return {"message": "Service is up and running."}


@app.get("/version")
async def get_version() -> dict[str, str]:
    return {
        "frontend_version": settings.FRONTEND_VERSION,
        "backend_version": settings.BACKEND_VERSION,
    }


async def generate_similar_players_search_query_vector(player_name: str) -> list | None:
    try:
        query_vector, _ = await client.search_players_by_name(player_name.lower())
        return query_vector
    except Exception as e:
        logger.error(f"Error searching for player {player_name} embeddings in Qdrant: {e}")
        return None


async def fetch_user_input_player_stats(player_name: str) -> list | None:
    try:
        _, career_stats = await client.search_players_by_name(player_name.lower())
        return career_stats
    except Exception as e:
        logger.error(f"Error searching for player {player_name} stats in Qdrant: {e}")
        return None


async def handle_player_search_result(player_result, player_name) -> dict:
    if player_result.get("error"):
        return {
            "searched_player": {"target": player_result["target"], "player_name": player_name},
            "error": player_result["error"],
        }

    real_player_name = player_result["player_name"]
    logger.info(f"Received search query for real player name: {real_player_name} from user input: {player_name}")
    return {
        "searched_player": {"player_name": real_player_name},
        "error": None,
    }


@app.get("/user_requested_player_career_stats/")
async def user_requested_player_career_stats(player_name: str) -> dict | list:
    logger.info(f"Received request for career stats for player: {player_name}")
    player_name = player_name.lower()
    player_result = await asyncio.to_thread(get_real_player_name, player_name)

    result = await handle_player_search_result(player_result, player_name)
    if result["error"]:
        return result

    real_player_name = result["searched_player"]["player_name"]
    career_stats = await fetch_user_input_player_stats(real_player_name)
    if not career_stats:
        logger.error(f"Failed to retrieve career stats for player: {real_player_name}")
        return {"searched_player": player_result, "error": f"No career stats found for '{real_player_name}'"}
    logger.info(f"Retrieved career stats for player: {real_player_name}")
    logger.debug(f"Retrieved career stats: {career_stats}")
    return format_user_requested_player_career_stats(player_result, career_stats)


@app.get("/search_similar_players/")
async def search_similar_players(
    player_name: str,
    position: Optional[str] = None,
    era: Optional[str] = None,
) -> dict | list:
    player_name = player_name.lower()
    player_result = await asyncio.to_thread(get_real_player_name, player_name)

    result = await handle_player_search_result(player_result, player_name)
    if result["error"]:
        return result

    real_player_name = result["searched_player"]["player_name"]
    logger.info(
        f"Received search query for real player name: {real_player_name} from user input: {player_name}"
        f" with filters - position: {position}, era: {era}"
    )

    query_vector = await generate_similar_players_search_query_vector(real_player_name)
    if not query_vector:
        raise HTTPException(status_code=500, detail=f"Could not generate query vector for player '{real_player_name}'")

    search_result = await client.search_similar_players(query_vector, position=position, era=era)
    search_result = remove_same_player(search_result, real_player_name)
    if search_result:
        format_logger_search_result(search_result)
        logger.debug(f"Found results: {format_logger_search_result(search_result)}")
        return format_similar_players_search_result(player_result, search_result)
    else:
        logger.error(
            f"No results found for player '{real_player_name}' in collection '{client.collection_name}' from user input '{player_name}'"
        )
        return {"searched_player": {"target": real_player_name, "player_name": player_name}, "similar_players": []}


class RecordSearchRequest(BaseModel):
    player_name: str
    position: Optional[str] = None
    era: Optional[str] = None
    original_query: Optional[str] = None
    search_source: Optional[str] = None
    results_found: Optional[bool] = None
    client_ip: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    timezone: Optional[str] = None


@app.post("/record_search/")
async def record_search(body: RecordSearchRequest) -> dict:
    if not settings.RECENT_SEARCHES_ENABLED:
        return {"status": "disabled"}
    await asyncio.to_thread(
        recent_searches_store.record_search,
        player_name=body.player_name,
        position=body.position,
        era=body.era,
        original_query=body.original_query,
        search_source=body.search_source,
        results_found=body.results_found,
        client_ip=body.client_ip,
        country=body.country,
        region=body.region,
        city=body.city,
        timezone=body.timezone,
    )
    return {"status": "ok"}


@app.get("/recent_searches/")
async def get_recent_searches(limit: int = Query(default=10, gt=0, le=50)) -> dict:
    if not settings.RECENT_SEARCHES_ENABLED:
        return {"recent_searches": []}
    searches = await asyncio.to_thread(recent_searches_store.get_recent_searches, limit)
    return {"recent_searches": searches}
