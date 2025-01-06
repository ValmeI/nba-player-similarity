from backend.utils.app_logger import logger
from backend.utils.fuzz_utils import find_all_potential_matches
import os
from backend.config import settings
from pprint import pformat


def get_player_from_aliases(user_input_player_name: str) -> str:
    for player in PLAYERS_ALIASES:
        logger.debug(f"Checking aliases for player: {player} and user input: {user_input_player_name}")
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
    return potential_matches


def get_real_player_name(user_input_player_name: str) -> dict:
    potential_matches = get_player_from_local_files(user_input_player_name, settings.RAW_NBA_DATA_PATH)
    
    # idea is that if user input is too vague, we return potential matches and ask user to be more specific
    if potential_matches.get("error"):
        return potential_matches
        
    all_matches = []
    if potential_matches:
        first_full_name = potential_matches["potential_matches"][0]["full_name"]
    else:
        first_full_name = user_input_player_name
        
    if potential_matches:
        logger.debug(
            f"Potential matches from local files for {user_input_player_name}: \n{pformat(potential_matches, indent=1)}"
        )
        for match in potential_matches["potential_matches"]:
            player_name = match["full_name"]
            alias_match = get_player_from_aliases(player_name)
            if alias_match:
                all_matches.append(alias_match)
                return {"target": user_input_player_name, "player_name": alias_match}

    if not all_matches:
        alias_match = get_player_from_aliases(user_input_player_name)
        if alias_match:
            all_matches.append(alias_match)
            
    final_full_name = all_matches[0] if all_matches else first_full_name
    logger.debug(f"Final full name: {final_full_name} from user input: {user_input_player_name}")
    return {"target": user_input_player_name, "player_name": final_full_name}


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
            "Shaquille Oneal",
            "Shaquille ONeil",
        ],
    },
    {
        "full_name": "Kobe Bryant",
        "aliases": ["Black Mamba", "Koby Bryant", "Kobee Bryant", "Coby Bryant", "Kobe Brian"],
    },
    {
        "full_name": "LeBron James",
        "aliases": [
            "King James",
            "LBJ",
            "The Chosen One",
            "Labron James",
            "Le Bron James",
            "Leborn James",
            "Libran James",
        ],
    },
    {
        "full_name": "Michael Jordan",
        "aliases": [
            "MJ",
            "Air Jordan",
            "His Airness",
            "The GOAT",
            "Micheal Jordan",
            "Mikel Jordan",
            "Mike Jordan",
            "Michel Jordan",
        ],
    },
    {"full_name": "Tim Duncan", "aliases": ["The Big Fundamental", "Tim Dunkan", "Timm Duncan", "Tim Dunkin"]},
    {
        "full_name": "Allen Iverson",
        "aliases": ["The Answer", "AI", "Alan Iverson", "Allan Iverson", "A.Iverson", "Allen Iversen"],
    },
    {
        "full_name": "Kevin Durant",
        "aliases": ["KD", "Durantula", "Slim Reaper", "Kevin Durrant", "Kavin Durant", "Durant Kavin", "Kevin Duren"],
    },
    {
        "full_name": "Stephen Curry",
        "aliases": [
            "Steph",
            "Chef Curry",
            "Baby-Faced Assassin",
            "Stephan Curry",
            "Steven Curry",
            "Step Curry",
            "Stefen Curry",
        ],
    },
    {
        "full_name": "Magic Johnson",
        "aliases": ["Magic", "Magik Johnson", "Majic Johnson", "Magick Johnson", "Magc Johnson"],
    },
    {
        "full_name": "Larry Bird",
        "aliases": ["The Hick from French Lick", "Larry Legend", "Lary Bird", "Larry Byrd", "Larry Baird"],
    },
    {
        "full_name": "Wilt Chamberlain",
        "aliases": ["Wilt the Stilt", "The Big Dipper", "Wlt Chamberlain", "Wilt Chamberlin", "Wilt Chambarlain"],
    },
    {
        "full_name": "Kareem Abdul-Jabbar",
        "aliases": ["Cap", "The Tower from Power", "Karem Abdul-Jabar", "Karim Abdul Jabbar", "Kareem AbdulJabbar"],
    },
    {
        "full_name": "Dirk Nowitzki",
        "aliases": ["The German Wunderkind", "Dirk Diggler", "Dirck Nowitski", "Derk Nowitzky", "Dirk Nowitsky"],
    },
    {"full_name": "Hakeem Olajuwon", "aliases": ["The Dream", "Hakim Olajuwon", "Hakeen Olajuwan", "Hakeem Olajuwan"]},
    {
        "full_name": "Charles Barkley",
        "aliases": ["Sir Charles", "The Round Mound of Rebound", "Charles Barkly", "Chales Barkley", "Charles Barley"],
    },
    {"full_name": "Dwyane Wade", "aliases": ["Flash", "D-Wade", "Dwayne Wade", "Duane Wade", "Dwayn Wade"]},
    {"full_name": "Chris Paul", "aliases": ["CP3", "The Point God", "Chris Pal", "Cris Paul", "Christopher Paul"]},
    {"full_name": "Paul Pierce", "aliases": ["The Truth", "Paul Pearce", "Pual Pierce", "Paul Pears"]},
    {
        "full_name": "Russell Westbrook",
        "aliases": ["Brodie", "Russel Westbrook", "Russell Westbrok", "Russell Westbrooke"],
    },
    {"full_name": "James Harden", "aliases": ["The Beard", "James Hardin", "Jams Harden", "James Hardeen"]},
    {"full_name": "Kyrie Irving", "aliases": ["Uncle Drew", "Kyrie Erving", "Kiry Irving", "Kairie Irving"]},
    {
        "full_name": "Damian Lillard",
        "aliases": ["Dame", "Dame Time", "Damion Lillard", "Damyan Lillard", "Damian Lilerd"],
    },
    {
        "full_name": "Giannis Antetokounmpo",
        "aliases": ["The Greek Freak", "Giannis Antetokoumpo", "Giannis Antentokounmpo", "Giannis Antetekounmpo"],
    },
    {"full_name": "Carmelo Anthony", "aliases": ["Melo", "Carmello Anthony", "Caramelo Anthony", "Carmelo Antony"]},
    {"full_name": "Anthony Davis", "aliases": ["AD", "The Brow", "Anthony Davies", "Antony Davis", "Anthony Daves"]},
    {"full_name": "Luka Doncic", "aliases": ["Luka Magic", "The Don", "Luca Doncic", "Luka Donchic", "Luka Donic"]},
    {"full_name": "Devin Booker", "aliases": ["Book", "D-Book", "Devon Booker", "Deven Booker", "Devin Boker"]},
    {"full_name": "Zion Williamson", "aliases": ["Zanos", "Zian Williamson", "Zion Willamson", "Zion Willimson"]},
    {"full_name": "Joel Embiid", "aliases": ["The Process", "Joel Embeid", "Joelle Embiid", "Joel Embid"]},
    {"full_name": "Penny Hardaway", "aliases": ["Penny", "Anfernee Hardaway", "Anferny Hardaway", "Penny Hardway"]},
    {"full_name": "Tracy McGrady", "aliases": ["T-Mac", "Tracy McGradey", "Tracey McGrady", "Tracy McCrady"]},
    {"full_name": "Patrick Ewing", "aliases": ["Ewing", "Pat Ewing", "Patrick Ewings", "Patrick Ewin"]},
    {"full_name": "Scottie Pippen", "aliases": ["Pip", "Scottie Pippin", "Scotty Pippen", "Scotie Pippen"]},
    {"full_name": "Grant Hill", "aliases": ["Hill", "G Hill", "Grant Hills", "Grant Hil"]},
    {"full_name": "Vince Carter", "aliases": ["Vinsanity", "Half-Man Half-Amazing", "Vince Carters", "Vince Cartr"]},
    {"full_name": "Ray Allen", "aliases": ["Jesus Shuttlesworth", "Ray Ray", "Ray Allens", "Ray Alen"]},
    {"full_name": "Paul George", "aliases": ["PG13", "Paul Georges", "Paul Gorge", "Paul Georg"]},
    {"full_name": "Jimmy Butler", "aliases": ["Jimmy Buckets", "Jimmy Butlers", "J Butler", "Jimmy Butlar"]},
    {"full_name": "Jayson Tatum", "aliases": ["JT", "J Tatum", "Jason Tatum", "Jayson Tatam"]},
    {"full_name": "Bradley Beal", "aliases": ["Beal", "Brad Beal", "Bradly Beal", "Bradley Bale"]},
]
