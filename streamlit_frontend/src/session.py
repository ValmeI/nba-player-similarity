import streamlit as st

from shared.config import settings
from shared.utils.app_logger import logger
from streamlit_frontend.src.utils import get_client_ip, get_geolocation


def initialize_session_state() -> None:
    if "messages" not in st.session_state:
        # Replace literal \n from env with markdown line breaks (two trailing spaces + newline)
        initial_message = settings.STREAMLIT_INITIAL_MESSAGE.replace("\\n", "  \n")
        st.session_state["messages"] = [{"role": "assistant", "content": initial_message}]
    if "user_input" not in st.session_state:
        st.session_state["user_input"] = ""
    if "last_processed_input" not in st.session_state:
        st.session_state["last_processed_input"] = ""

    if "client_ip" not in st.session_state:
        st.session_state["client_ip"] = get_client_ip()

    if "client_geolocation" not in st.session_state:
        st.session_state["client_geolocation"] = get_geolocation(st.session_state["client_ip"])

    geolocation = st.session_state["client_geolocation"]
    log_message = (
        f"🌍 User Location Info: "
        f" - 🏷️ IP Address: {st.session_state['client_ip']} "
        f" - 🌍 Country: {geolocation.get('country', 'Unknown')} "
        f" - 🏙️ City: {geolocation.get('city', 'Unknown')} "
        f" - 📍 Region: {geolocation.get('region', 'Unknown')} "
        f" - 🌐 ISP: {geolocation.get('isp', 'Unknown')} "
        f" - 🗺️ Coordinates: {geolocation.get('latitude', 'Unknown')}, {geolocation.get('longitude', 'Unknown')} "
        f" - 🌍 Continent: {geolocation.get('continent', 'Unknown')} "
        f" - 🕒 Timezone: {geolocation.get('timezone', 'Unknown')} "
        f" - 💱 Currency: {geolocation.get('currency', 'Unknown')} "
        f" - 🏢 Organization: {geolocation.get('org', 'Unknown')}"
    )
    logger.info(log_message)
