import os
from dotenv import load_dotenv

load_dotenv()

# Works both locally (.env) and on Streamlit Cloud (st.secrets)
try:
    import streamlit as st
    API_KEY  = st.secrets["API_KEY"]
    DB_HOST  = st.secrets["DB_HOST"]
    DB_USER  = st.secrets["DB_USER"]
    DB_PASSWORD = st.secrets["DB_PASSWORD"]
    DB_NAME_VAL = st.secrets["DB_NAME"]
except Exception:
    API_KEY  = os.getenv("API_KEY")
    DB_HOST  = os.getenv("DB_HOST")
    DB_USER  = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_NAME_VAL = os.getenv("DB_NAME")

API_HOST = "aerodatabox.p.rapidapi.com"

HEADERS = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": API_HOST
}

DB_CONFIG = {
    "host": DB_HOST,
    "port": 3306,
    "user": DB_USER,
    "password": DB_PASSWORD,
    "use_pure": True
}

DB_NAME = DB_NAME_VAL

