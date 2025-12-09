import streamlit as st
import pandas as pd
import requests
from dateutil import parser
from io import StringIO
import logging
import constants as C

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def parse_datetime_any(s: str):
    if pd.isna(s):
        return None
    try:
        return parser.parse(str(s), dayfirst=True)
    except Exception:
        try:
            return parser.parse(str(s), dayfirst=False)
        except Exception:
            return None


def to_float_any(x):
    try:
        return float(str(x).replace(",", "."))
    except Exception:
        return float("nan")


def validate_columns(df: pd.DataFrame, required: list[str]) -> bool:
    missing = [c for c in required if c not in df.columns]
    if missing:
        logger.error(f"Missing columns: {missing}")
        st.error(f"Erro: Colunas faltando na planilha: {', '.join(missing)}")
        return False
    return True


def process_column(df: pd.DataFrame, src: str, dest: str, func=None, default=None):
    if src in df.columns:
        if func:
            df[dest] = df[src].apply(func)
        else:
            df[dest] = df[src]
    else:
        df[dest] = default


@st.cache_data(show_spinner=False, ttl=3600)
def load_sheet(sheet_id: str, sheet_name: str) -> pd.DataFrame:
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    try:
        logger.info(f"Loading sheet: {sheet_name}")
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        df = pd.read_csv(StringIO(r.text))
        return df
    except Exception as e:
        logger.error(f"Error loading {sheet_name}: {e}")
        st.error(f"Erro ao carregar aba '{sheet_name}': {e}")
        return pd.DataFrame()


@st.cache_data(show_spinner=False, ttl=3600)
def get_dados(sheet_id: str) -> pd.DataFrame:
    df = load_sheet(sheet_id, "Dados")
    if df.empty:
        return df

    process_column(df, C.COL_SRC_TIMESTAMP, C.COL_INT_DT, parse_datetime_any)
    process_column(
        df, C.COL_SRC_STATUS, C.COL_INT_STATUS, lambda x: str(x).strip().upper(), ""
    )
    process_column(
        df, C.COL_SRC_CAPTADOR, C.COL_INT_CAPTADOR, lambda x: str(x).strip(), ""
    )
    process_column(
        df, C.COL_SRC_STATE, C.COL_INT_STATE, lambda x: str(x).strip().upper(), ""
    )
    process_column(df, C.COL_SRC_CITY, C.COL_INT_CITY, lambda x: str(x).strip(), "")
    process_column(df, C.COL_SRC_CEP, C.COL_INT_CEP, lambda x: str(x).strip(), "")
    process_column(
        df,
        C.COL_SRC_CONTRACT_TYPE,
        C.COL_INT_CONTRACT_TYPE,
        lambda x: str(x).strip(),
        "",
    )

    try:
        df[C.COL_INT_PARTNER] = df.iloc[:, 0].astype(str).str.strip()
    except Exception:
        df[C.COL_INT_PARTNER] = ""

    if C.COL_INT_DT in df.columns:
        df[C.COL_INT_DT] = pd.to_datetime(df[C.COL_INT_DT], errors="coerce")

    # Map Regions
    if C.COL_INT_STATE in df.columns:
        df[C.COL_INT_REGION] = df[C.COL_INT_STATE].map(C.ESTADO_REGIAO).fillna("Outros")

    return df


@st.cache_data(show_spinner=False, ttl=3600)
def get_faturamento(sheet_id: str) -> pd.DataFrame:
    df = load_sheet(sheet_id, "FATURAMENTO")
    if df.empty:
        return df

    process_column(df, C.COL_SRC_VALOR, C.COL_INT_VALOR, to_float_any, 0.0)
    process_column(
        df,
        C.COL_SRC_COMISSAO,
        C.COL_INT_COMISSAO,
        lambda x: to_float_any(x) / 100.0,
        0.0,
    )
    process_column(df, C.COL_SRC_DATA, C.COL_INT_DATA, parse_datetime_any, None)
    process_column(
        df,
        C.COL_SRC_FINANCIAL_TYPE,
        C.COL_INT_FINANCIAL_TYPE,
        lambda x: str(x).strip().upper(),
        "",
    )
    process_column(
        df,
        C.COL_SRC_CONTRACT_TYPE,
        C.COL_INT_CONTRACT_TYPE,
        lambda x: str(x).strip(),
        "",
    )

    if C.COL_INT_DATA in df.columns:
        df[C.COL_INT_DATA] = pd.to_datetime(df[C.COL_INT_DATA], errors="coerce")

    return df
