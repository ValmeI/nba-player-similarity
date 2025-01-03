from backend.utils.app_logger import logger
from backend.utils.fuzz_utils import find_all_potential_matches
import os
from backend.config import settings
from icecream import ic

PLAYERS_ALIASES = [
    {
        "full_name": "Shaquille O'Neal",
        "aliases": [
            "Shaq",
            "Diesel",
            "Big Aristotle",
            "Superman",
            "Big Cactus",
            "Shaquill O'Neil",
            "Shaquil O'Neal",
            "Shaqueil O'Neal",
        ],
    },
    {"full_name": "Kobe Bryant", "aliases": ["Black Mamba", "Koby Bryant", "Kobee Bryant", "Coby Bryant"]},
    {
        "full_name": "LeBron James",
        "aliases": ["King James", "LBJ", "The Chosen One", "Labron James", "Le Bron James", "Leborn James"],
    },
    {
        "full_name": "Michael Jordan",
        "aliases": ["MJ", "Air Jordan", "His Airness", "The GOAT", "Micheal Jordan", "Mikel Jordan", "Mike Jordan"],
    },
    {"full_name": "Tim Duncan", "aliases": ["The Big Fundamental", "Tim Dunkan", "Timm Duncan"]},
    {"full_name": "Allen Iverson", "aliases": ["The Answer", "AI", "Alan Iverson", "Allan Iverson", "A.Iverson"]},
    {
        "full_name": "Kevin Durant",
        "aliases": ["KD", "Durantula", "Slim Reaper", "Kevin Durrant", "Kavin Durant", "Durant Kavin"],
    },
    {
        "full_name": "Stephen Curry",
        "aliases": ["Steph", "Chef Curry", "Baby-Faced Assassin", "Stephan Curry", "Steven Curry", "Step Curry"],
    },
    {"full_name": "Magic Johnson", "aliases": ["Magic", "Magik Johnson", "Majic Johnson", "Magick Johnson"]},
    {"full_name": "Larry Bird", "aliases": ["The Hick from French Lick", "Larry Legend", "Lary Bird", "Larry Byrd"]},
    {
        "full_name": "Wilt Chamberlain",
        "aliases": ["Wilt the Stilt", "The Big Dipper", "Wlt Chamberlain", "Wilt Chamberlin"],
    },
    {
        "full_name": "Kareem Abdul-Jabbar",
        "aliases": ["Cap", "The Tower from Power", "Karem Abdul-Jabar", "Karim Abdul Jabbar"],
    },
    {
        "full_name": "Dirk Nowitzki",
        "aliases": ["The German Wunderkind", "Dirk Diggler", "Dirck Nowitski", "Derk Nowitzky"],
    },
    {"full_name": "Hakeem Olajuwon", "aliases": ["The Dream", "Hakim Olajuwon", "Hakeen Olajuwan"]},
    {
        "full_name": "Charles Barkley",
        "aliases": ["Sir Charles", "The Round Mound of Rebound", "Charles Barkly", "Chales Barkley"],
    },
    {"full_name": "Dwyane Wade", "aliases": ["Flash", "D-Wade", "Dwayne Wade", "Duane Wade"]},
    {"full_name": "Chris Paul", "aliases": ["CP3", "The Point God", "Chris Pal", "Cris Paul"]},
    {"full_name": "Paul Pierce", "aliases": ["The Truth", "Paul Pearce", "Pual Pierce"]},
    {"full_name": "Russell Westbrook", "aliases": ["Brodie", "Russel Westbrook", "Russell Westbrok"]},
    {"full_name": "James Harden", "aliases": ["The Beard", "James Hardin", "Jams Harden"]},
    {"full_name": "Kyrie Irving", "aliases": ["Uncle Drew", "Kyrie Erving", "Kiry Irving"]},
    {"full_name": "Damian Lillard", "aliases": ["Dame", "Dame Time", "Damion Lillard", "Damyan Lillard"]},
    {
        "full_name": "Giannis Antetokounmpo",
        "aliases": ["The Greek Freak", "Giannis Antetokoumpo", "Giannis Antentokounmpo"],
    },
    {"full_name": "Carmelo Anthony", "aliases": ["Melo", "Carmello Anthony", "Caramelo Anthony"]},
    {"full_name": "Anthony Davis", "aliases": ["AD", "The Brow", "Anthony Davies", "Antony Davis"]},
    {"full_name": "Luka Doncic", "aliases": ["Luka Magic", "The Don", "Luca Doncic", "Luka Donchic"]},
    {"full_name": "Devin Booker", "aliases": ["Book", "D-Book", "Devon Booker", "Deven Booker"]},
    {"full_name": "Zion Williamson", "aliases": ["Zanos", "Zian Williamson", "Zion Willamson"]},
    {"full_name": "Joel Embiid", "aliases": ["The Process", "Joel Embeid", "Joelle Embiid"]},
    {"full_name": "Penny Hardaway", "aliases": ["Penny", "Anfernee Hardaway", "Anferny Hardaway"]},
    {"full_name": "Tracy McGrady", "aliases": ["T-Mac", "Tracy McGradey", "Tracey McGrady"]},
    {"full_name": "Patrick Ewing", "aliases": ["Ewing", "Pat Ewing", "Patrick Ewings"]},
    {"full_name": "Scottie Pippen", "aliases": ["Pip", "Scottie Pippin", "Scotty Pippen"]},
    {"full_name": "Grant Hill", "aliases": ["Hill", "G Hill", "Grant Hills"]},
    {"full_name": "Vince Carter", "aliases": ["Vinsanity", "Half-Man Half-Amazing", "Vince Carters"]},
    {"full_name": "Ray Allen", "aliases": ["Jesus Shuttlesworth", "Ray Ray", "Ray Allens"]},
    {"full_name": "Paul George", "aliases": ["PG13", "Paul Georges", "Paul Gorge"]},
    {"full_name": "Jimmy Butler", "aliases": ["Jimmy Buckets", "Jimmy Butlers", "J Butler"]},
    {"full_name": "Jayson Tatum", "aliases": ["JT", "J Tatum", "Jason Tatum"]},
    {"full_name": "Bradley Beal", "aliases": ["Beal", "Brad Beal", "Bradly Beal"]},
]


def get_player_from_aliases(user_input_player_name: str) -> str:
    for player in PLAYERS_ALIASES:
        if player["full_name"].lower() == user_input_player_name.lower():
            logger.info(f'Exact match found for "{player["full_name"]}" of user input "{user_input_player_name}"')
            return player["full_name"]
        elif any(alias.lower() == user_input_player_name.lower() for alias in player["aliases"]):
            logger.info(f'Full match found for "{player["full_name"]}" of user input "{user_input_player_name}"')
            return player["full_name"]
    logger.debug(f'No aliases match found for "{user_input_player_name}"')
    return None


def get_player_from_local_files(user_input_player_name: str, data_dir: str):
    files: list = os.listdir(data_dir)
    potential_matches = find_all_potential_matches(user_input_player_name, files, settings.FUZZ_THRESHOLD_LOCAL_NAME)
    logger.info(f"Potential matches from local files for {user_input_player_name}: {potential_matches}")
    return potential_matches


def get_real_player_name(user_input_player_name: str):
    potential_matches = get_player_from_local_files(user_input_player_name, settings.RAW_NBA_DATA_PATH)
    all_matches = []

    if potential_matches:
        logger.debug(f"Potential matches from local files for {user_input_player_name}: {potential_matches}")
        for match in potential_matches["potential_matches"]:
            alias_match = get_player_from_aliases(match)
            if alias_match:
                all_matches.append(alias_match)

    if not all_matches:
        alias_match = get_player_from_aliases(user_input_player_name)
        if alias_match:
            all_matches.append(alias_match)

    return all_matches[0] if all_matches else None


ic(get_real_player_name("leborn"))
ic(get_real_player_name("kobe"))
ic(get_real_player_name("shaquille"))
ic(get_real_player_name("shaq"))
