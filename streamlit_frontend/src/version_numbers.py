import requests
from shared.config import settings

# Backend version endpoint
BACKEND_VERSION_ENDPOINT = f"http://{settings.FAST_API_HOST}:{settings.FAST_API_PORT}/version"


def fetch_versions():
    try:
        response = requests.get(BACKEND_VERSION_ENDPOINT, timeout=settings.API_REQUEST_TIMEOUT)
        response.raise_for_status()
        version_data = response.json()
        frontend_version = version_data.get("frontend_version", "Unknown")
        backend_version = version_data.get("backend_version", "Unknown")
    except requests.RequestException:
        frontend_version = "Error fetching version"
        backend_version = "Error fetching version"
    return frontend_version, backend_version
