from backend.src.store_data import store_embeddings_to_qdrant


if __name__ == "__main__":
    data_path = "data/transactions.csv"  # TODO: make it so it can ingest multiple files
    collection_name = "transactions"  # TODO: move it to config
    store_embeddings_to_qdrant(collection_name, data_path)
