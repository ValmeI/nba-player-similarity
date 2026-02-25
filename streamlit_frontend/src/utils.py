import requests
import streamlit as st
from shared.config import settings

BACKEND_VERSION_ENDPOINT = f"http://{settings.FAST_API_HOST}:{settings.FAST_API_PORT}/version"


@st.cache_data(ttl=300)
def fetch_versions() -> tuple[str, str]:
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


def get_client_ip() -> str:
    try:
        headers = st.context.headers
        forwarded_for = headers.get("X-Forwarded-For", "")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        real_ip = headers.get("X-Real-Ip", "")
        if real_ip:
            return real_ip.strip()
        return "Unknown"
    except Exception:
        return "Unknown"


def get_geolocation(ip) -> dict:
    try:
        geo_data = requests.get(f"https://ipwhois.app/json/{ip}", timeout=settings.API_REQUEST_TIMEOUT).json()
        return {
            "ip": ip,
            "country": geo_data.get("country", "Unknown"),
            "city": geo_data.get("city", "Unknown"),
            "region": geo_data.get("region", "Unknown"),
            "latitude": geo_data.get("latitude"),
            "longitude": geo_data.get("longitude"),
            "isp": geo_data.get("isp", "Unknown"),
            "continent": geo_data.get("continent", "Unknown"),
            "timezone": geo_data.get("timezone", "Unknown"),
            "currency": geo_data.get("currency", "Unknown"),
            "org": geo_data.get("org", "Unknown"),
        }
    except:  # pylint: disable=bare-except
        return {
            "ip": ip,
            "country": "Unknown",
            "city": "Unknown",
            "region": "Unknown",
            "latitude": None,
            "longitude": None,
            "isp": "Unknown",
            "continent": "Unknown",
            "timezone": "Unknown",
            "currency": "Unknown",
            "org": "Unknown",
        }
