#from fastapi import FastAPI
from backend.src.search_api import app as search_app  # Import FastAPI pbject from search_api

# Kui soovid `app` defineerida otse:
# app = FastAPI()

# Lae olemasolev app
app = search_app

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
