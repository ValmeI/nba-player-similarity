import json
from openai import OpenAI
from shared.config import settings
from shared.utils.app_logger import logger

client = OpenAI(api_key=settings.LLM_API_KEY)

INTENT_SYSTEM_PROMPT = """You are an NBA query parser. Given a user's natural language input, extract structured information.

Return a JSON object with these fields:
- "player_name": The NBA player's name mentioned (string or null if no player is identified)
- "era": The decade/era mentioned (e.g., "1990s", "2000s", "2010s", "2020s") or null if not specified
- "position": The position mentioned, normalized to one of: "Guard", "Forward", "Center", or null if not specified
- "multiple_players": true if multiple player names are mentioned, false otherwise

Position mapping hints:
- "big men", "bigs", "centers" -> "Center"
- "wings", "small forwards", "power forwards" -> "Forward"
- "guards", "point guards", "shooting guards", "backcourt" -> "Guard"
- "scorers", "shooters", "playmakers" -> null (these are play styles, not positions)

Era mapping hints:
- "90s", "the nineties" -> "1990s"
- "2000s", "the aughts" -> "2000s"
- "modern", "today", "current" -> "2020s"
- "80s" -> "1980s"

If multiple players are mentioned, set "player_name" to the first player mentioned and "multiple_players" to true.
If the input is just a player name with no filters, return the name with null for era and position.

Always return valid JSON only, no extra text."""


def parse_user_intent(user_input: str) -> dict:
    """Parse natural language user input into structured search parameters.

    Returns a dict with keys: player_name, era, position, multiple_players.
    Falls back to treating input as a plain player name if LLM call fails.
    """
    default_result = {
        "player_name": user_input.strip() or None,
        "era": None,
        "position": None,
        "multiple_players": False,
    }

    try:
        response = client.chat.completions.create(
            model=settings.LLM_MODEL_NAME,
            messages=[
                {"role": "system", "content": INTENT_SYSTEM_PROMPT},
                {"role": "user", "content": user_input},
            ],
            max_tokens=settings.LLM_INTENT_MAX_TOKENS,
            temperature=settings.LLM_INTENT_TEMPERATURE,
        )

        raw_output = response.choices[0].message.content.strip()
        logger.info(f"Intent parser raw output: {raw_output}")

        parsed = json.loads(raw_output)

        if not isinstance(parsed, dict):
            logger.warning(f"Intent parser returned non-dict JSON: {type(parsed)}. Falling back to plain input.")
            return default_result

        return {
            "player_name": parsed.get("player_name") or None,
            "era": parsed.get("era") or None,
            "position": parsed.get("position") or None,
            "multiple_players": bool(parsed.get("multiple_players", False)),
        }

    except json.JSONDecodeError as e:
        logger.warning(f"Intent parser returned invalid JSON: {e}. Falling back to plain input.")
        return default_result
    except Exception as e:
        logger.warning(f"Intent parser failed: {e}. Falling back to plain input.")
        return default_result
