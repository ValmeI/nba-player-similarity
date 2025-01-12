from backend.src.search_api import app as search_app
from shared.config import settings
import uvicorn

# this needs to be outside the if __name__ == "__main__" block, as this needs to be defined in module level
app = search_app

if __name__ == "__main__":
    uvicorn.run(
        "backend.run_backend_server_main:app",
        host=settings.FAST_API_HOST,
        port=settings.FAST_API_PORT,
        reload=True,  # Enable auto-reload on code changes during development
    )
