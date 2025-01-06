from rapidfuzz import process
from backend.utils.app_logger import logger
from pprint import pformat


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
        potential_matches.extend({"full_name": match, "score": 100} for match in exact_matches)
        logger.info(f"Exact matches found for {target}: \n{pformat(exact_matches, indent=1)}")
        return {"target": target, "potential_matches": potential_matches}
    else:
        results = process.extract(target, candidates, score_cutoff=threshold)
        logger.info(f"Found {len(results)} matches for {target}: \n{pformat(results, indent=1)}")

        potential_matches.extend([{"full_name": result[0], "score": result[1]} for result in results])
        result: dict = {"target": target, "potential_matches": potential_matches}
        return result
