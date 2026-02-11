import requests
import streamlit as st
import unicodedata
import logging
import constants as C

logger = logging.getLogger(__name__)


def normalize_string(s: str) -> str:
    """
    Normalizes a string by lowercasing and removing accents.

    Args:
        s (str): The string to normalize.

    Returns:
        str: The normalized string.
    """
    if not isinstance(s, str):
        return ""
    return (
        "".join(
            c
            for c in unicodedata.normalize("NFD", s)
            if unicodedata.category(c) != "Mn"
        )
        .lower()
        .strip()
    )


@st.cache_data(ttl=86400)  # Cache for 24h
def get_all_municipios():
    """
    Fetches all municipalities from IBGE to build a lookup table.

    Returns:
        list: A list of dictionaries containing municipality data from IBGE.
    """
    try:
        response = requests.get(C.API_URL_IBGE_MUNICIPIOS)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error fetching IBGE municipalities: {e}")
        return []


@st.cache_data(ttl=86400)
def get_ibge_code(city: str, state: str) -> str:
    """
    Finds the IBGE code for a given city and state pair.

    Args:
        city (str): The city name.
        state (str): The state code (UF) or name.

    Returns:
        str | None: The IBGE code if found, otherwise None.
    """
    all_mun = get_all_municipios()

    norm_city = normalize_string(city)
    norm_state = normalize_string(state)

    for mun in all_mun:
        # Check state first (try standard path then alternative path)
        # Standard: mun['microrregiao']['mesorregiao']['UF']['sigla']
        # Alternative (New municipalities): mun['regiao-imediata']['regiao-intermediaria']['UF']['sigla']
        mun_state = None

        try:
            if mun.get("microrregiao"):
                mun_state = mun["microrregiao"]["mesorregiao"]["UF"]["sigla"]
            elif mun.get("regiao-imediata"):
                mun_state = mun["regiao-imediata"]["regiao-intermediaria"]["UF"][
                    "sigla"
                ]
        except (KeyError, TypeError):
            continue

        if mun_state and normalize_string(mun_state) == norm_state:
            if normalize_string(mun["nome"]) == norm_city:
                return str(mun["id"])

    return None


@st.cache_data(ttl=86400)
def get_municipality_geojson(ibge_code: str):
    """
    Fetches GeoJSON for a specific municipality code.

    Args:
        ibge_code (str): The IBGE municipality code.

    Returns:
        dict | None: The GeoJSON data if found, otherwise None.
    """
    if not ibge_code:
        return None

    url = C.API_URL_IBGE_MALHA_MUNICIPO.format(id=ibge_code)
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error fetching GeoJSON for {ibge_code}: {e}")
        return None
