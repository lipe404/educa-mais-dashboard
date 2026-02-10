import streamlit as st
import pandas as pd
import requests
from dateutil import parser
from io import StringIO
import logging
from datetime import datetime
from typing import Tuple
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
        st.error(C.ERR_MSG_MISSING_COLUMNS.format(columns=", ".join(missing)))
        return False
    return True


def process_column(
    df: pd.DataFrame,
    src: str,
    dest: str,
    func=None,
    default=None,
    aliases: list = None,
    index: int = None,
):
    # Determine the actual source column name
    actual_src = None
    if src in df.columns:
        actual_src = src
    elif aliases:
        # Try exact aliases
        for alias in aliases:
            if alias in df.columns:
                actual_src = alias
                break
        # Try case-insensitive matching
        if not actual_src:
            for col in df.columns:
                if str(col).strip().upper() == src.upper():
                    actual_src = col
                    break
                for alias in aliases:
                    if str(col).strip().upper() == alias.upper():
                        actual_src = col
                        break

    # Fallback to index if provided and still not found
    if not actual_src and index is not None:
        if 0 <= index < len(df.columns):
            actual_src = df.columns[index]
            logger.info(
                f"Column '{src}' not found by name. Using index {index} (name: '{actual_src}')"
            )

    if actual_src:
        if func:
            try:
                df[dest] = df[actual_src].apply(func)
            except Exception as e:
                logger.error(f"Error processing column {actual_src} -> {dest}: {e}")
                df[dest] = default
        else:
            df[dest] = df[actual_src]
    else:
        logger.warning(
            f"Column '{src}' not found (aliases={aliases}, index={index}). Using default."
        )
        df[dest] = default


@st.cache_data(show_spinner=False, ttl=600)
def load_sheet(
    sheet_id: str, sheet_name: str, gid: str = None
) -> Tuple[pd.DataFrame, datetime]:
    if gid:
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    else:
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"

    try:
        logger.info(f"Loading sheet: {sheet_name} (GID: {gid})")
        r = requests.get(url, timeout=10)
        r.raise_for_status()

        # Use utf-8-sig to handle BOM if present
        r.encoding = "utf-8-sig"

        df = pd.read_csv(StringIO(r.text))

        # Clean headers: strip whitespace and BOM artifacts
        df.columns = df.columns.str.strip().str.replace("\ufeff", "")

        return df, datetime.now()
    except Exception as e:
        logger.error(f"Error loading {sheet_name}: {e}")
        st.error(C.ERR_MSG_LOADING_SHEET.format(sheet_name=sheet_name, error=e))
        return pd.DataFrame(), datetime.now()


@st.cache_data(show_spinner=False, ttl=600)
def get_dados(sheet_id: str) -> Tuple[pd.DataFrame, datetime]:
    df, ts = load_sheet(sheet_id, C.SHEET_NAME_DATA)
    if df.empty:
        return df, ts

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
        df[C.COL_INT_REGION] = (
            df[C.COL_INT_STATE].map(C.ESTADO_REGIAO).fillna(C.DEFAULT_REGION_OTHER)
        )

    return df, ts


@st.cache_data(show_spinner=False, ttl=600)
def get_faturamento(sheet_id: str) -> Tuple[pd.DataFrame, datetime]:
    df, ts = load_sheet(sheet_id, C.SHEET_NAME_FINANCIAL)
    if df.empty:
        return df, ts

    # Process partner column (assuming it's in column A, index 0)
    try:
        df[C.COL_INT_PARTNER] = df.iloc[:, 0].astype(str).str.strip()
    except Exception:
        df[C.COL_INT_PARTNER] = ""

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

    return df, ts


@st.cache_data(show_spinner=False, ttl=600)
def get_alunos(sheet_id: str) -> Tuple[pd.DataFrame, datetime]:
    df, ts = load_sheet(sheet_id, C.SHEET_NAME_STUDENTS, gid=C.GID_STUDENTS)
    if df.empty:
        return df, ts

    # Map columns based on CSV structure
    # 0: PARCEIRO, 1: TIPO, 2: DATA, 3: NOME DO ALUNO, 4: CURSO
    # 5: CPF, 6: DOCUMENTOS, 7: SISTEC, 8: CARTEIRINHA

    process_column(
        df,
        C.COL_SRC_PARTNER,
        C.COL_INT_PARTNER,
        lambda x: str(x).strip(),
        "",
        aliases=["Parceiro", "parceiro", "PARCEIRO"],
        index=0,
    )
    process_column(
        df,
        C.COL_SRC_FINANCIAL_TYPE,
        C.COL_INT_FINANCIAL_TYPE,
        lambda x: str(x).strip().upper(),
        "",
        aliases=["Tipo", "tipo", "TIPO"],
        index=1,
    )
    process_column(
        df,
        C.COL_SRC_DATA,
        C.COL_INT_DATA,
        parse_datetime_any,
        None,
        aliases=["Data", "data", "DATA"],
        index=2,
    )
    process_column(
        df,
        C.COL_SRC_STUDENT_NAME,
        C.COL_INT_STUDENT_NAME,
        lambda x: str(x).strip(),
        "",
        aliases=["Nome", "Aluno", "Nome do Aluno", "ALUNO", "NOME", "NOME DO ALUNO"],
        index=3,
    )
    process_column(
        df,
        C.COL_SRC_COURSE,
        C.COL_INT_COURSE,
        lambda x: str(x).strip(),
        "",
        aliases=["Curso", "curso", "CURSO"],
        index=4,
    )
    process_column(
        df,
        C.COL_SRC_CPF,
        C.COL_INT_CPF,
        lambda x: str(x).strip(),
        "",
        aliases=["CPF", "cpf"],
        index=5,
    )
    process_column(
        df,
        C.COL_SRC_DOCUMENTS,
        C.COL_INT_DOCUMENTS,
        lambda x: str(x).strip(),
        "",
        aliases=["Documentos", "documentos", "DOCUMENTOS"],
        index=6,
    )
    process_column(
        df,
        C.COL_SRC_SISTEC,
        C.COL_INT_SISTEC,
        lambda x: str(x).strip(),
        "",
        aliases=["Sistec", "sistec", "SISTEC"],
        index=7,
    )
    process_column(
        df,
        C.COL_SRC_CARD,
        C.COL_INT_CARD,
        lambda x: str(x).strip(),
        "",
        aliases=["Carteirinha", "carteirinha", "CARTEIRINHA"],
        index=8,
    )

    # Filter out empty rows based on Student Name or Course
    df = df[
        df[C.COL_INT_STUDENT_NAME].notna()
        & (df[C.COL_INT_STUDENT_NAME] != "")
        & (df[C.COL_INT_STUDENT_NAME] != "nan")
    ]

    if C.COL_INT_DATA in df.columns:
        df[C.COL_INT_DATA] = pd.to_datetime(df[C.COL_INT_DATA], errors="coerce")

    return df, ts


@st.cache_data(show_spinner=False, ttl=600)
def get_students_general_data(sheet_id: str) -> Tuple[pd.DataFrame, datetime]:
    df, ts = load_sheet(
        sheet_id, C.SHEET_NAME_STUDENTS_GENERAL, gid=C.GID_STUDENTS_GENERAL
    )
    if df.empty:
        return df, ts

    # Map columns
    process_column(
        df,
        C.COL_SRC_GEN_FIRST_NAME,
        C.COL_INT_GEN_FIRST_NAME,
        lambda x: str(x).strip(),
        "",
        aliases=["First Name"],
        index=0,
    )
    process_column(
        df,
        C.COL_SRC_GEN_LAST_NAME,
        C.COL_INT_GEN_LAST_NAME,
        lambda x: str(x).strip(),
        "",
        aliases=["Last Name"],
        index=1,
    )
    process_column(
        df,
        C.COL_SRC_GEN_CPF,
        C.COL_INT_GEN_CPF,
        lambda x: str(x).strip(),
        "",
        aliases=["cpf", "CPF"],
        index=2,
    )
    process_column(
        df,
        C.COL_SRC_GEN_PHONE,
        C.COL_INT_GEN_PHONE,
        lambda x: str(x).strip(),
        "",
        aliases=["phone", "Phone", "Telefone"],
        index=3,
    )
    process_column(
        df,
        C.COL_SRC_GEN_EMAIL,
        C.COL_INT_GEN_EMAIL,
        lambda x: str(x).strip(),
        "",
        aliases=["email", "Email"],
        index=4,
    )
    process_column(
        df,
        C.COL_SRC_GEN_ZIP,
        C.COL_INT_GEN_ZIP,
        lambda x: str(x).strip(),
        "",
        aliases=["zip", "CEP", "Cep"],
        index=5,
    )
    process_column(
        df,
        C.COL_SRC_GEN_CITY,
        C.COL_INT_GEN_CITY,
        lambda x: str(x).strip(),
        "",
        aliases=["cidade", "Cidade"],
        index=6,
    )
    process_column(
        df,
        C.COL_SRC_GEN_STATE,
        C.COL_INT_GEN_STATE,
        lambda x: str(x).strip().upper(),
        "",
        aliases=["estado", "Estado"],
        index=7,
    )
    process_column(
        df,
        C.COL_SRC_GEN_ADDRESS,
        C.COL_INT_GEN_ADDRESS,
        lambda x: str(x).strip(),
        "",
        aliases=["endereço", "Endereço", "endereco"],
        index=8,
    )
    process_column(
        df,
        C.COL_SRC_GEN_NEIGHBORHOOD,
        C.COL_INT_GEN_NEIGHBORHOOD,
        lambda x: str(x).strip(),
        "",
        aliases=["bairro", "Bairro"],
        index=9,
    )
    process_column(
        df,
        C.COL_SRC_GEN_COUNTRY,
        C.COL_INT_GEN_COUNTRY,
        lambda x: str(x).strip(),
        "",
        aliases=["Country", "País"],
        index=10,
    )

    # Clean rows with empty or invalid city/state
    if C.COL_INT_GEN_CITY in df.columns:
        df[C.COL_INT_GEN_CITY] = df[C.COL_INT_GEN_CITY].astype(str).str.strip()
    if C.COL_INT_GEN_STATE in df.columns:
        df[C.COL_INT_GEN_STATE] = (
            df[C.COL_INT_GEN_STATE].astype(str).str.strip().str.upper()
        )

    if C.COL_INT_GEN_CITY in df.columns and C.COL_INT_GEN_STATE in df.columns:
        mask_valid_city = (df[C.COL_INT_GEN_CITY] != "") & (
            ~df[C.COL_INT_GEN_CITY].str.lower().isin(["nan", "none"])
        )
        mask_valid_state = (df[C.COL_INT_GEN_STATE] != "") & (
            ~df[C.COL_INT_GEN_STATE].str.lower().isin(["nan", "none"])
        )
        df = df[mask_valid_city & mask_valid_state]

    # Map Regions based on State
    if C.COL_INT_GEN_STATE in df.columns:
        # Ensure state abbreviations are clean (2 chars usually)
        # Some sheets might have full names, but ESTADO_REGIAO keys are 2 chars (UF).
        # We might need to handle full names if the sheet has them.
        # Assuming UFs for now as per "estado".
        df[C.COL_INT_REGION] = (
            df[C.COL_INT_GEN_STATE].map(C.ESTADO_REGIAO).fillna(C.DEFAULT_REGION_OTHER)
        )

    return df, ts
