# from fastapi import FastAPI
from backend.src.search_api import app as search_app  # Import FastAPI object from search_api

# in case we want to use FastAPI directly
# app = FastAPI()

# load search_app
app = search_app

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)


# TODO: Redis player cache?
# TODO: add async to search api
# TODO: use yield when processing and reading parquet
