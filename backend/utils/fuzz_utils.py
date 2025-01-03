from rapidfuzz import process
from backend.utils.app_logger import logger


def find_top_matches(target: str, candidates: list, threshold: int = 80) -> str:
    results = process.extractOne(target, candidates, score_cutoff=threshold)
    logger.info(f"Found {len(results)} matches for {target} with threshold {threshold}: {results}")
    return results[0]


def find_all_potential_matches(target: str, candidates: list, threshold: int) -> tuple:
    potential_matches = []
    target = target.lower()
    candidates = [candidate.lower().rsplit("_", 2)[0].replace("_", " ") for candidate in candidates]
    exact_matches = [candidate for candidate in candidates if target in candidate]

    if exact_matches:
        logger.info(f"Exact matches found for {target}: {exact_matches}")
        potential_matches.extend(exact_matches)

    results = process.extract(target, candidates, score_cutoff=threshold)
    logger.info(f"Found {len(results)} matches for {target}: {results}")

    potential_matches.extend([match[0] for match in results])
    result: dict = {"target": target, "potential_matches": potential_matches}
    return result
