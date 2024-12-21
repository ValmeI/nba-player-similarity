from rapidfuzz import process
from backend.utils.app_logger import logger


def find_top_matches(target: str, candidates: list, threshold: int = 80) -> str:
    results = process.extractOne(target, candidates, score_cutoff=threshold)
    logger.info(f"Found {len(results)} matches for {target} with threshold {threshold}: {results}")
    return results[0]
