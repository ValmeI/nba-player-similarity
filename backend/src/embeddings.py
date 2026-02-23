import numpy as np
import pandas as pd
from sklearn.preprocessing import RobustScaler
from shared.utils.app_logger import logger

pd.set_option("future.no_silent_downcasting", True)


METADATA_COLUMNS = ["PLAYER_NAME", "PLAYER_ID", "LAST_PLAYED_SEASON", "POSITION"]

NUMERIC_COLUMNS = [
    "PTS_RESPONSIBILITY",  # Points responsibility
    "LAST_PLAYED_AGE",  # Age when the player last played
    "TOTAL_SEASONS",  # Total number of seasons played
    "GP",  # Games Played
    "GS",  # Games Started
    "PTS_PER_GAME",  # Points per game
    "REB_PER_GAME",  # Rebounds per game
    "AST_PER_GAME",  # Assists per game
    "STL_PER_GAME",  # Steals per game
    "BLK_PER_GAME",  # Blocks per game
    "TOV_PER_GAME",  # Turnovers per game
    "MIN_PER_GAME",  # Minutes per game
    "TS%",  # True shooting percentage
    "EFG%",  # Effective field goal percentage
    "FG%",  # Field goal percentage
    "3P%",  # Three point percentage
    "FT%",  # Free throw percentage
    "PER",  # Player efficiency rating
    "WS/48",  # Win shares per 48 minutes
    "USG%",  # Usage rate
    "PTS_PER_36",  # Points per 36 minutes
    "AST_TO_RATIO",  # Assist-to-turnover ratio
    "STL%",  # Steal percentage
    "BLK%",  # Block percentage
]


NORMALIZED_COLUMN_PREFIX = "NORM_"
TO_NORMALIZED_COLUMNS = [f"{NORMALIZED_COLUMN_PREFIX}{col}" for col in NUMERIC_COLUMNS]


POSITION_COLUMNS = ["POS_GUARD", "POS_FORWARD", "POS_CENTER"]
POSITION_WEIGHT = 3.0


class PlayerEmbeddings:
    def __init__(self, players_stats_df: pd.DataFrame):
        self.players_stats_df = players_stats_df

    def encode_position(self) -> pd.DataFrame:
        """
        One-hot encode the POSITION column into POS_GUARD, POS_FORWARD, POS_CENTER.
        Compound positions like "Guard-Forward" set multiple bits to 1.
        "Unknown" or missing positions result in all zeros.
        """
        pos_col = self.players_stats_df["POSITION"].fillna("Unknown")
        self.players_stats_df["POS_GUARD"] = pos_col.str.contains("Guard", na=False).astype(int)
        self.players_stats_df["POS_FORWARD"] = pos_col.str.contains("Forward", na=False).astype(int)
        self.players_stats_df["POS_CENTER"] = pos_col.str.contains("Center", na=False).astype(int)
        return self.players_stats_df

    def fill_missing_values(self) -> pd.DataFrame:
        """
        Fill missing values in numeric columns with 0 as those are really old players
        """
        self.players_stats_df[NUMERIC_COLUMNS] = self.players_stats_df[NUMERIC_COLUMNS].fillna(0)
        return self.players_stats_df

    def normalize_features(self) -> pd.DataFrame:
        result_df = self.players_stats_df.copy()
        scaler = RobustScaler()

        normalized_data = scaler.fit_transform(self.players_stats_df[NUMERIC_COLUMNS])

        # Add all normalized columns at once using a new DataFrame
        normalized_df = pd.DataFrame(
            normalized_data, columns=[f"NORM_{col}" for col in NUMERIC_COLUMNS], index=self.players_stats_df.index
        )

        result_df = pd.concat([result_df, normalized_df], axis=1)

        logger.debug(f"Raw career stats before normalization:\n{self.players_stats_df[NUMERIC_COLUMNS]}")
        logger.debug(f"Normalized career stats:\n{result_df[[f'NORM_{col}' for col in NUMERIC_COLUMNS]]}")

        return result_df

    def create_players_embeddings(self) -> pd.DataFrame:
        logger.debug(f"Raw numeric data before normalization:\n{self.players_stats_df[NUMERIC_COLUMNS]}")
        missing_columns = [col for col in NUMERIC_COLUMNS if col not in self.players_stats_df.columns]

        if missing_columns:
            raise ValueError(f"Missing required columns for processing: {missing_columns}")

        self.fill_missing_values()
        if "POSITION" not in self.players_stats_df.columns:
            logger.warning("POSITION column missing from DataFrame - all position encodings will be zero")
        self.encode_position()
        self.players_stats_df = self.normalize_features()

        norm_values = self.players_stats_df[TO_NORMALIZED_COLUMNS].values
        pos_values = self.players_stats_df[POSITION_COLUMNS].values * POSITION_WEIGHT
        all_embeddings = np.hstack([norm_values, pos_values])
        self.players_stats_df["embeddings"] = [row.tolist() for row in all_embeddings]
        return self.players_stats_df[METADATA_COLUMNS + ["embeddings"] + NUMERIC_COLUMNS + TO_NORMALIZED_COLUMNS]
