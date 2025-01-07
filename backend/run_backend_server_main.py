"""
NBA Player Similarity Backend Server Runner

This script starts the FastAPI backend server that powers the NBA player similarity search.
It serves as the main entry point for running the backend service that the Streamlit 
frontend communicates with.

The server provides REST API endpoints for:
- Player similarity search
- Player data retrieval
- (Add other main functionalities here)

To run the backend server:
    $ c

The server will start on based on the settings in the configuration file. Following are the localhost endpoints:
- URL: http://127.0.0.1:8000
- API docs: http://127.0.0.1:8000/docs (Swagger UI)
"""

from backend.src.search_api import app as search_app
from backend.config import settings

# Initialize the FastAPI application
app = search_app

if __name__ == "__main__":
    import uvicorn
    
    # Run the FastAPI server
    uvicorn.run(
        "backend.run_backend_server_main:app",
        host=settings.FAST_API_HOST,
        port=settings.FAST_API_PORT,
        reload=True,  # Enable auto-reload on code changes during development
    )

# Future Improvements:
# TODO: Implement Redis cache for player data to improve response times
# TODO: Add async processing for search operations
# TODO: Optimize parquet file reading with yield statements for better memory usage
