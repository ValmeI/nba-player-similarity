from openai import OpenAI
from shared.config import settings

client = OpenAI(api_key=settings.LLM_API_KEY)


def generate_analysis(user_req_players_stats: list, similar_player_stats: list):
    user_player = user_req_players_stats[0]["player_name"]
    similar_players = [player["player_name"] for player in similar_player_stats]

    context = (
        f"Compare {user_player} to {', '.join(similar_players)} based on their playing styles and stats. "
        "Provide a short paragraph explaining how they are similar or different, focusing on scoring, rebounding, defense, "
        "and other shared strengths. Highlight {user_player}'s unique qualities in relation to the others. "
        "Ensure the response has multiple sentences and is complete."
    )

    response = client.chat.completions.create(
        model=settings.LLM_MODEL_NAME,
        messages=[
            {"role": "system", "content": settings.LLM_PROMPT_TEMPLATE},
            {"role": "user", "content": context},
        ],
        max_tokens=settings.LLM_MAX_TOKENS,
        temperature=settings.LLM_TEMPERATURE,
    )

    output = response.choices[0].message.content.strip()

    # Ensure output ends with a complete sentence
    if not output.endswith((".", "!", "?")):
        output = output.rsplit(".", 1)[0] + "."

    return output
