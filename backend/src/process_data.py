# CSV andmete töötlemine ja embeddingute loomine

import pandas as pd
from sentence_transformers import SentenceTransformer
from icecream import ic

IMPORTANT_COLUMNS = ["Date", "Description", "Amount", "Sender/receiver name"]


def load_and_process_csv(file_path: str) -> pd.DataFrame:
    df = pd.read_csv(file_path)

    df = df[IMPORTANT_COLUMNS]

    if IMPORTANT_COLUMNS != list(df.columns):
        raise Exception(f"Needed columns: {IMPORTANT_COLUMNS}. Found columns: {list(df.columns)}")

    # create embeddings
    model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    df["embeddings"] = df["Description"].apply(lambda x: model.encode(str(x)).tolist())

    ic("First 5 rows of processed data:")
    ic(df.head())

    return df
