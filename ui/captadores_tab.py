import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import re
import unicodedata
import os
import json
import constants as C




def _check_authentication(access_key: str) -> bool:
    """
    Handles access control for the Captadores tab by verifying the provided access key.

    Args:
        access_key (str): The expected correct access key.

    Returns:
        bool: True if the user enters the correct key, False otherwise.
    """
    key = st.text_input(
        C.UI_LABEL_ACCESS_KEY, type="password", key="captadores_access_key"
    )
    if key != access_key:
        st.warning(C.UI_LABEL_ENTER_KEY_MSG)
        return False
    return True


def _format_captador_name(name) -> str:
    """
    Helper function to clean and title case captador names.
    Handles the undefined placeholder.

    Args:
        name (Any): The raw captador name.

    Returns:
        str: The standardized name.
    """
    if pd.isna(name):
        return C.UI_LABEL_UNIDENTIFIED
    name_str = str(name).strip()
    if name_str == "" or name_str.lower() == C.UI_LABEL_UNIDENTIFIED.lower():
        return C.UI_LABEL_UNIDENTIFIED
    return name_str.title()


def _strip_accents(s: str) -> str:
    """
    Strips accents/diacritics from a string.
    """
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')


def _clean_partner_name(name: str) -> str:
    """
    Standardizes a partner name by removing CNPJ/CPF prefixes, hidden characters,
    accents, punctuation/symbols, and converting to uppercase.
    """
    if not isinstance(name, str):
        return ""
    name = name.replace('\u2060', '')
    name = name.strip().upper()
    cleaned = _strip_accents(name)
    
    # Replace non-alphanumeric (including punctuation) with space
    cleaned = re.sub(r'[^A-Z0-9\s]', ' ', cleaned)
    
    # Remove prefix composed of digits and spaces at the start
    cleaned = re.sub(r'^[0-9\s]+', '', cleaned)
    
    # Remove multiple spaces/newlines
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip()



def _find_best_captador(fat_partner: str, partner_map: pd.DataFrame) -> str:
    """
    Fuzzy matches a faturamento partner name against the partner-captador map.
    Returns the captador name or None.
    """
    if not isinstance(fat_partner, str) or partner_map.empty:
        return None
    
    cleaned_fat = _clean_partner_name(fat_partner)
    if not cleaned_fat:
        return None

    # Self-heal if _cleaned_partner is missing
    if "_cleaned_partner" not in partner_map.columns and C.COL_INT_PARTNER in partner_map.columns:
        partner_map = partner_map.copy()
        partner_map["_cleaned_partner"] = partner_map[C.COL_INT_PARTNER].apply(_clean_partner_name)

    # 1. Exact match
    exact_match = partner_map[partner_map["_cleaned_partner"] == cleaned_fat]
    if not exact_match.empty:
        return exact_match.iloc[0][C.COL_INT_CAPTADOR]


    # 2. Substring match (minimum length 6 to prevent single-letter/short word noise matches)
    candidates = []
    for _, row in partner_map.iterrows():
        cleaned_dados = row["_cleaned_partner"]
        if len(cleaned_fat) >= 6 and len(cleaned_dados) >= 6:
            if cleaned_fat in cleaned_dados or cleaned_dados in cleaned_fat:
                candidates.append((row[C.COL_INT_CAPTADOR], cleaned_dados))

    if candidates:
        # Prefer the one with closest length
        candidates.sort(key=lambda x: abs(len(x[1]) - len(cleaned_fat)))
        return candidates[0][0]

    # 3. Word-by-word intersection match
    COMMON_WORDS = {
        # Common Brazilian last names
        "SILVA", "SANTOS", "OLIVEIRA", "SOUZA", "RODRIGUES", "FERREIRA", "ALVES", 
        "GOMES", "LIMA", "COSTA", "ROCHA", "BARBOSA", "RIBEIRO", "MARTINS", "CARVALHO",
        "TEIXEIRA", "FREITAS", "CAMPOS", "AZEVEDO", "CANDIDO", "ANDRADE", "PINTO",
        "DIAS", "MOREIRA", "NUNES", "VIEIRA", "CARDOSO", "MACHADO", "MENDES",
        
        # Common first names
        "MARIA", "JOSE", "ANTONIO", "FRANCISCO", "CARLOS", "PAULO", "PEDRO", 
        "LUCAS", "LUIZ", "MARCOS", "ANA", "JOAO", "ANDRE", "VICENTE", "GABRIEL", 
        "BRUNO", "FELIPE", "MATEUS", "JULIA", "BEATRIZ", "ALICE", "TIAGO", "ROBERTO",
        
        # Common company/polo/institution terms
        "EIRELI", "LTDA", "MEI", "POLO", "CENTRO", "CURSO", "ENSINO", "EDUCACIONAL", 
        "GRUPO", "INSTITUTO", "COGNITIVA", "EMOCIONA", "EAD", "ONLINE", "PRO", "DIGITAL",
        "NEGOCIOS", "ASSOCIACAO", "SEGURANCA", "INTEGRADO", "INTERATIVO", "CONSULTORIA",
        "PARTNER", "PARCEIRO", "PARCEIROS",
        
        # Common words and states
        "RIO", "JANEIRO", "SUL", "NORTE", "LESTE", "OESTE", "GRANDE", "MINAS", "GERAIS",
        "SAO", "PAULO", "SANTA", "CATARINA", "PARANA", "BAHIA", "CEARA", "PERNAMBUCO",
        "BRASIL", "NOVA", "IGUACU"
    }

    fat_words = [w for w in cleaned_fat.split() if len(w) >= 3]
    if fat_words:
        word_candidates = []
        for _, row in partner_map.iterrows():
            cleaned_dados = row["_cleaned_partner"]
            dados_words = [w for w in cleaned_dados.split() if len(w) >= 3]
            intersection = set(fat_words).intersection(set(dados_words))
            if intersection:
                # If only 1 word matches, it must not be a common word/stopword
                if len(intersection) == 1:
                    matched_word = list(intersection)[0]
                    if matched_word in COMMON_WORDS:
                        continue
                word_candidates.append((row[C.COL_INT_CAPTADOR], len(intersection), cleaned_dados))
        
        if word_candidates:
            # Sort by number of matching words descending, then by shortest length diff
            word_candidates.sort(key=lambda x: (-x[1], abs(len(x[2]) - len(cleaned_fat))))
            return word_candidates[0][0]

    return None


def _load_partner_overrides() -> dict:
    """
    Loads manual partner-captador overrides from a persistent JSON file.
    """
    path = "partner_captador_overrides.json"
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_partner_overrides(overrides: dict):
    """
    Saves manual partner-captador overrides to a persistent JSON file.
    """
    path = "partner_captador_overrides.json"
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(overrides, f, indent=4, ensure_ascii=False)
    except Exception:
        pass


def _get_unmatched_partners(fat_df: pd.DataFrame, partner_map: pd.DataFrame) -> list:
    """
    Finds all unique partner names in faturamento that cannot be automatically mapped
    and do not have a manual override yet.
    """
    if fat_df.empty:
        return []
    
    overrides = _load_partner_overrides()
    unique_partners = fat_df[C.COL_INT_PARTNER].dropna().unique()
    
    unmatched = []
    for p in unique_partners:
        p_str = str(p).strip()
        if not p_str or p_str.lower() == "nan" or p_str in overrides:
            continue
        
        captador = _find_best_captador(p_str, partner_map)
        if not captador:
            unmatched.append(p_str)
            
    return sorted(unmatched)


def _get_faturamento_captador_map(fat_df: pd.DataFrame, partner_map: pd.DataFrame) -> dict:
    """
    Creates a mapping dictionary of faturamento partner names to captador names.
    Uses manual overrides first, then falls back to fuzzy matching.
    """
    if fat_df.empty:
        return {}
    
    overrides = _load_partner_overrides()
    
    unique_partners = fat_df[C.COL_INT_PARTNER].dropna().unique()
    mapping = {}
    for p in unique_partners:
        p_str = str(p).strip()
        if not p_str:
            continue
        
        # 1. Check manual overrides first
        if p_str in overrides:
            mapping[p_str] = overrides[p_str]
        else:
            # 2. Fallback to fuzzy matching
            captador = _find_best_captador(p_str, partner_map)
            mapping[p_str] = captador if captador else C.UI_LABEL_UNIDENTIFIED
            
    return mapping



@st.cache_data(show_spinner=False, ttl=600)
def _aggregate_partner_captador_map(raw_dados: pd.DataFrame) -> pd.DataFrame:
    """
    Creates a unique mapping between partners and their respective captadores from raw_dados.
    Includes a standardized cleaned partner column for robust matching.

    Args:
        raw_dados (pd.DataFrame): The raw, unfiltered dados DataFrame.

    Returns:
        pd.DataFrame: A DataFrame with columns [C.COL_INT_PARTNER, C.COL_INT_CAPTADOR, "_cleaned_partner"].
    """
    if raw_dados.empty:
        return pd.DataFrame(columns=[C.COL_INT_PARTNER, C.COL_INT_CAPTADOR, "_cleaned_partner"])

    # Select partner and captador columns
    df_map = raw_dados[[C.COL_INT_PARTNER, C.COL_INT_CAPTADOR]].copy()

    # Drop rows where partner is null or empty
    df_map[C.COL_INT_PARTNER] = df_map[C.COL_INT_PARTNER].astype(str).str.strip()
    df_map = df_map[df_map[C.COL_INT_PARTNER] != ""]

    # Clean captador name (strip)
    df_map[C.COL_INT_CAPTADOR] = df_map[C.COL_INT_CAPTADOR].astype(str).str.strip()
    df_map = df_map[df_map[C.COL_INT_CAPTADOR] != ""]

    # Add cleaned partner column
    df_map["_cleaned_partner"] = df_map[C.COL_INT_PARTNER].apply(_clean_partner_name)
    df_map = df_map[df_map["_cleaned_partner"] != ""]

    # Drop duplicates on the cleaned name to guarantee 1-to-1 match
    df_map = df_map.drop_duplicates(subset=["_cleaned_partner"])

    return df_map



@st.cache_data(show_spinner=False, ttl=600)
def _aggregate_captured_partners(dados_df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates unique partners captured by captador for contracts with status ASSINADO.

    Args:
        dados_df (pd.DataFrame): The filtered dados DataFrame.

    Returns:
        pd.DataFrame: Aggregated DataFrame with unique partners count by captador.
    """
    if dados_df.empty:
        return pd.DataFrame(columns=[C.UI_LABEL_CAPTADOR_COLUMN, C.UI_LABEL_PARTNERS_CAPTURED_COLUMN])

    # Clean data
    df_clean = dados_df.dropna(subset=[C.COL_INT_CAPTADOR, C.COL_INT_PARTNER, C.COL_INT_STATUS])
    df_clean = df_clean[
        (df_clean[C.COL_INT_CAPTADOR].astype(str).str.strip() != "") &
        (df_clean[C.COL_INT_PARTNER].astype(str).str.strip() != "") &
        (df_clean[C.COL_INT_STATUS].astype(str).str.strip() == C.STATUS_ASSINADO)
    ]

    if df_clean.empty:
        return pd.DataFrame(columns=[C.UI_LABEL_CAPTADOR_COLUMN, C.UI_LABEL_PARTNERS_CAPTURED_COLUMN])

    df_clean["captador_display"] = df_clean[C.COL_INT_CAPTADOR].apply(_format_captador_name)
    df_clean["partner_display"] = df_clean[C.COL_INT_PARTNER].astype(str).str.strip()

    df_grouped = df_clean.groupby("captador_display")["partner_display"].nunique().reset_index()
    df_grouped.columns = [C.UI_LABEL_CAPTADOR_COLUMN, C.UI_LABEL_PARTNERS_CAPTURED_COLUMN]
    df_grouped = df_grouped.sort_values(by=C.UI_LABEL_PARTNERS_CAPTURED_COLUMN, ascending=False)
    return df_grouped


@st.cache_data(show_spinner=False, ttl=600)
def _aggregate_waiting_contracts(dados_df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates count of contracts waiting signature by captador for contracts with status AGUARDANDO.

    Args:
        dados_df (pd.DataFrame): The filtered dados DataFrame.

    Returns:
        pd.DataFrame: Aggregated DataFrame with count of waiting contracts by captador.
    """
    if dados_df.empty:
        return pd.DataFrame(columns=[C.UI_LABEL_CAPTADOR_COLUMN, C.UI_LABEL_WAITING_CONTRACTS_COLUMN])

    # Clean data
    df_clean = dados_df.dropna(subset=[C.COL_INT_CAPTADOR, C.COL_INT_STATUS])
    df_clean = df_clean[
        (df_clean[C.COL_INT_CAPTADOR].astype(str).str.strip() != "") &
        (df_clean[C.COL_INT_STATUS].astype(str).str.strip() == C.STATUS_AGUARDANDO)
    ]

    if df_clean.empty:
        return pd.DataFrame(columns=[C.UI_LABEL_CAPTADOR_COLUMN, C.UI_LABEL_WAITING_CONTRACTS_COLUMN])

    df_clean["captador_display"] = df_clean[C.COL_INT_CAPTADOR].apply(_format_captador_name)

    df_grouped = df_clean.groupby("captador_display").size().reset_index(name=C.UI_LABEL_WAITING_CONTRACTS_COLUMN)
    df_grouped.columns = [C.UI_LABEL_CAPTADOR_COLUMN, C.UI_LABEL_WAITING_CONTRACTS_COLUMN]
    df_grouped = df_grouped.sort_values(by=C.UI_LABEL_WAITING_CONTRACTS_COLUMN, ascending=False)
    return df_grouped


@st.cache_data(show_spinner=False, ttl=600)
def _aggregate_revenue_by_captador(fat_df: pd.DataFrame, partner_captador_map: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates total revenue and sales count by captador.

    Args:
        fat_df (pd.DataFrame): The filtered faturamento DataFrame.
        partner_captador_map (pd.DataFrame): Mapping of partner to captador.

    Returns:
        pd.DataFrame: Aggregated DataFrame with revenue metrics by captador.
    """
    if fat_df.empty:
        return pd.DataFrame(columns=[C.UI_LABEL_CAPTADOR_COLUMN, C.UI_LABEL_REVENUE_COLUMN, "Contratos"])

    df_fat = fat_df.copy()
    df_fat[C.COL_INT_PARTNER] = df_fat[C.COL_INT_PARTNER].astype(str).str.strip()
    df_fat = df_fat[df_fat[C.COL_INT_PARTNER] != ""]

    fat_captador_map = _get_faturamento_captador_map(df_fat, partner_captador_map)
    df_fat["Captador"] = df_fat[C.COL_INT_PARTNER].map(fat_captador_map)
    df_fat["Captador"] = df_fat["Captador"].apply(_format_captador_name)

    # Aggregate
    df_grouped = df_fat.groupby("Captador").agg(
        faturamento=(C.COL_INT_VALOR, "sum"),
        contratos=(C.COL_INT_VALOR, "count")
    ).reset_index()

    df_grouped.columns = [C.UI_LABEL_CAPTADOR_COLUMN, C.UI_LABEL_REVENUE_COLUMN, "Contratos"]
    df_grouped = df_grouped.sort_values(by=C.UI_LABEL_REVENUE_COLUMN, ascending=False)

    return df_grouped


def _render_captured_partners_chart(df: pd.DataFrame) -> None:
    """
    Renders a bar chart showing the number of unique partners captured by each captador.

    Args:
        df (pd.DataFrame): Aggregated DataFrame with unique partners count by captador.
    """
    if df.empty:
        st.info(C.UI_LABEL_NO_DATA_PERIOD)
        return

    fig = px.bar(
        df,
        x=C.UI_LABEL_CAPTADOR_COLUMN,
        y=C.UI_LABEL_PARTNERS_CAPTURED_COLUMN,
        title=C.UI_LABEL_CAPTADORES_PERF_TITLE,
        labels={
            C.UI_LABEL_CAPTADOR_COLUMN: C.UI_LABEL_CAPTADOR_COLUMN,
            C.UI_LABEL_PARTNERS_CAPTURED_COLUMN: C.UI_LABEL_PARTNER_UNIQUE,
        },
        color=C.UI_LABEL_PARTNERS_CAPTURED_COLUMN,
        color_continuous_scale=px.colors.sequential.Pinkyl,
        text_auto=True,
    )
    fig.update_layout(
        xaxis_tickangle=-45,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#8a8d9a"),
        coloraxis_showscale=False
    )
    st.plotly_chart(fig, width="stretch")


def _render_waiting_contracts_chart(df: pd.DataFrame) -> None:
    """
    Renders a bar chart showing the count of waiting contracts by captador.

    Args:
        df (pd.DataFrame): Aggregated DataFrame with count of waiting contracts by captador.
    """
    if df.empty:
        st.info(C.UI_LABEL_NO_DATA_PERIOD)
        return

    fig = px.bar(
        df,
        x=C.UI_LABEL_CAPTADOR_COLUMN,
        y=C.UI_LABEL_WAITING_CONTRACTS_COLUMN,
        title=C.UI_LABEL_CAPTADORES_WAITING_TITLE,
        labels={
            C.UI_LABEL_CAPTADOR_COLUMN: C.UI_LABEL_CAPTADOR_COLUMN,
            C.UI_LABEL_WAITING_CONTRACTS_COLUMN: C.UI_LABEL_CONTRACTS_WAITING,
        },
        color=C.UI_LABEL_WAITING_CONTRACTS_COLUMN,
        color_continuous_scale=px.colors.sequential.Blues,
        text_auto=True,
    )
    fig.update_layout(
        xaxis_tickangle=-45,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#8a8d9a"),
        coloraxis_showscale=False
    )
    st.plotly_chart(fig, width="stretch")


def _render_revenue_chart(df: pd.DataFrame) -> None:
    """
    Renders a bar chart showing the total revenue generated by each captador.

    Args:
        df (pd.DataFrame): Aggregated DataFrame with faturamento by captador.
    """
    if df.empty:
        st.info(C.UI_LABEL_NO_DATA_PERIOD)
        return

    fig = px.bar(
        df,
        x=C.UI_LABEL_CAPTADOR_COLUMN,
        y=C.UI_LABEL_REVENUE_COLUMN,
        title=C.UI_LABEL_CAPTADORES_REVENUE_TITLE,
        labels={
            C.UI_LABEL_CAPTADOR_COLUMN: C.UI_LABEL_CAPTADOR_COLUMN,
            C.UI_LABEL_REVENUE_COLUMN: C.UI_LABEL_REVENUE_TOTAL,
        },
        color=C.UI_LABEL_REVENUE_COLUMN,
        color_continuous_scale=px.colors.sequential.Pinkyl,
        text_auto=".2f",
    )
    fig.update_layout(
        xaxis_tickangle=-45,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#8a8d9a"),
        coloraxis_showscale=False
    )
    st.plotly_chart(fig, width="stretch")


def _aggregate_ticket_medio_by_captador(fat_df: pd.DataFrame, partner_captador_map: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates faturamento divided by number of unique partners (ticket médio por parceiro) by captador.

    Args:
        fat_df (pd.DataFrame): The filtered faturamento DataFrame.
        partner_captador_map (pd.DataFrame): Mapping of partner to captador.

    Returns:
        pd.DataFrame: Aggregated DataFrame with ticket médio by captador.
    """
    if fat_df.empty:
        return pd.DataFrame(columns=[C.UI_LABEL_CAPTADOR_COLUMN, C.UI_LABEL_TICKET_MEDIO_COLUMN])

    df_fat = fat_df.copy()
    df_fat[C.COL_INT_PARTNER] = df_fat[C.COL_INT_PARTNER].astype(str).str.strip()
    df_fat = df_fat[df_fat[C.COL_INT_PARTNER] != ""]

    fat_captador_map = _get_faturamento_captador_map(df_fat, partner_captador_map)
    df_fat["Captador"] = df_fat[C.COL_INT_PARTNER].map(fat_captador_map)
    df_fat["Captador"] = df_fat["Captador"].apply(_format_captador_name)

    # Group by Captador and Partner to get total faturamento per partner
    partner_grouped = df_fat.groupby(["Captador", C.COL_INT_PARTNER]).agg(
        faturamento_parceiro=(C.COL_INT_VALOR, "sum")
    ).reset_index()

    # Group by Captador to get total faturamento and count of unique partners
    captador_grouped = partner_grouped.groupby("Captador").agg(
        total_faturamento=("faturamento_parceiro", "sum"),
        qtd_parceiros=("faturamento_parceiro", "count")
    ).reset_index()

    # Calculate Ticket Médio
    captador_grouped[C.UI_LABEL_TICKET_MEDIO_COLUMN] = captador_grouped["total_faturamento"] / captador_grouped["qtd_parceiros"]

    # Sort by Ticket Médio descending
    captador_grouped = captador_grouped.sort_values(by=C.UI_LABEL_TICKET_MEDIO_COLUMN, ascending=False)

    # Select columns
    df_result = captador_grouped[["Captador", C.UI_LABEL_TICKET_MEDIO_COLUMN]].copy()
    df_result.columns = [C.UI_LABEL_CAPTADOR_COLUMN, C.UI_LABEL_TICKET_MEDIO_COLUMN]

    return df_result


def _render_ticket_medio_chart(df: pd.DataFrame) -> None:
    """
    Renders a bar chart showing the ticket médio por parceiro for each captador.

    Args:
        df (pd.DataFrame): Aggregated DataFrame with ticket médio by captador.
    """
    if df.empty:
        st.info(C.UI_LABEL_NO_DATA_PERIOD)
        return

    fig = px.bar(
        df,
        x=C.UI_LABEL_CAPTADOR_COLUMN,
        y=C.UI_LABEL_TICKET_MEDIO_COLUMN,
        title=C.UI_LABEL_CAPTADORES_TICKET_TITLE,
        labels={
            C.UI_LABEL_CAPTADOR_COLUMN: C.UI_LABEL_CAPTADOR_COLUMN,
            C.UI_LABEL_TICKET_MEDIO_COLUMN: C.UI_LABEL_TICKET_MEDIO,
        },
        color=C.UI_LABEL_TICKET_MEDIO_COLUMN,
        color_continuous_scale=px.colors.sequential.Blues,
        text_auto=".2f",
    )
    fig.update_layout(
        xaxis_tickangle=-45,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#8a8d9a"),
        coloraxis_showscale=False
    )
    st.plotly_chart(fig, width="stretch")


@st.cache_data(show_spinner=False, ttl=600)
def _aggregate_radar_data(
    dados_filtered: pd.DataFrame,
    fat_filtered: pd.DataFrame,
    raw_dados: pd.DataFrame,
    tax_pct: float,
    captador_pct: float
) -> pd.DataFrame:
    """
    Aggregates performance metrics (partners captured, faturamento, conversion rate,
    ticket médio, accumulated commission) by captador for radar chart.

    Args:
        dados_filtered (pd.DataFrame): Filtered dados DataFrame.
        fat_filtered (pd.DataFrame): Filtered faturamento DataFrame.
        raw_dados (pd.DataFrame): Raw unfiltered dados DataFrame for static mapping.
        tax_pct (float): Global tax percentage.
        captador_pct (float): Captador commission percentage.

    Returns:
        pd.DataFrame: Aggregated metrics by captador.
    """
    MAIN_CAPTADORES = ["Leila", "Thais", "Ana Beatriz", "Fernanda", "Lorena Oliveira", "Luiza Martins"]

    # Initialize df with all 6 captadores to ensure they always show up
    df_res = pd.DataFrame({"Captador": MAIN_CAPTADORES})

    # 1. Parceiros Captados (ASSINADO)
    captured_df = _aggregate_captured_partners(dados_filtered)
    df_res = pd.merge(df_res, captured_df, on="Captador", how="left").fillna(0)

    # 2. Conversão
    if not dados_filtered.empty and C.COL_INT_CAPTADOR in dados_filtered.columns and C.COL_INT_STATUS in dados_filtered.columns:
        df_status = dados_filtered.copy()
        df_status["captador_display"] = df_status[C.COL_INT_CAPTADOR].apply(_format_captador_name)

        status_grouped = df_status.groupby(["captador_display", C.COL_INT_STATUS]).size().unstack(fill_value=0).reset_index()
        status_grouped.columns.name = None

        # Ensure status columns exist
        for col in [C.STATUS_ASSINADO, C.STATUS_AGUARDANDO]:
            if col not in status_grouped.columns:
                status_grouped[col] = 0

        status_grouped["total"] = status_grouped[C.STATUS_ASSINADO] + status_grouped[C.STATUS_AGUARDANDO]
        status_grouped["Conversão"] = (status_grouped[C.STATUS_ASSINADO] / status_grouped["total"] * 100.0).fillna(0.0)

        status_grouped = status_grouped[["captador_display", "Conversão"]]
        status_grouped.columns = ["Captador", "Conversão"]
        df_res = pd.merge(df_res, status_grouped, on="Captador", how="left").fillna(0)
    else:
        df_res["Conversão"] = 0.0

    # 3. Faturamento
    partner_map = _aggregate_partner_captador_map(raw_dados)
    revenue_df = _aggregate_revenue_by_captador(fat_filtered, partner_map)
    df_res = pd.merge(df_res, revenue_df[["Captador", C.UI_LABEL_REVENUE_COLUMN]], on="Captador", how="left").fillna(0)
    df_res.rename(columns={C.UI_LABEL_REVENUE_COLUMN: "Faturamento"}, inplace=True)

    # 4. Ticket Médio
    ticket_df = _aggregate_ticket_medio_by_captador(fat_filtered, partner_map)
    df_res = pd.merge(df_res, ticket_df, on="Captador", how="left").fillna(0)
    df_res.rename(columns={C.UI_LABEL_TICKET_MEDIO_COLUMN: "Ticket Médio"}, inplace=True)

    # 5. Comissão Acumulada
    tax_rate = tax_pct / 100.0
    df_res["Comissão"] = df_res["Faturamento"] * (captador_pct / 100.0) * 0.5 * (1.0 - tax_rate)

    return df_res


def _render_radar_chart(df: pd.DataFrame) -> None:
    """
    Renders a radar chart comparing the 6 captadores across normalized metrics.

    Args:
        df (pd.DataFrame): Aggregated DataFrame with metrics by captador.
    """
    if df.empty:
        st.info(C.UI_LABEL_NO_DATA_PERIOD)
        return

    # Normalization (Maximum Scaling from 0 to 100)
    df_norm = df.copy()
    metrics = ["Parceiros Captados", "Faturamento", "Conversão", "Ticket Médio", "Comissão"]

    for metric in metrics:
        max_val = df_norm[metric].max()
        if max_val > 0:
            df_norm[metric + "_norm"] = (df_norm[metric] / max_val) * 100.0
        else:
            df_norm[metric + "_norm"] = 0.0

    categories = [
        C.UI_LABEL_PARTNERS_CAPTURED_COLUMN,
        C.UI_LABEL_REVENUE_TOTAL,
        "Taxa de Conversão",
        C.UI_LABEL_TICKET_MEDIO_COLUMN,
        "Comissão Acumulada"
    ]

    import plotly.graph_objects as go
    fig = go.Figure()

    colors_list = ["#ff2d95", "#2d9fff", "#00ff7f", "#ffaa00", "#9b5de5", "#f15bb5"]

    for idx, row in df_norm.iterrows():
        color = colors_list[idx % len(colors_list)]
        r_vals = [
            row["Parceiros Captados_norm"],
            row["Faturamento_norm"],
            row["Conversão_norm"],
            row["Ticket Médio_norm"],
            row["Comissão_norm"]
        ]
        # Close the loop path for radar chart
        r_vals.append(r_vals[0])
        theta_vals = categories + [categories[0]]

        fig.add_trace(go.Scatterpolar(
            r=r_vals,
            theta=theta_vals,
            fill='toself',
            name=row["Captador"],
            line=dict(color=color, width=2),
            fillcolor=color,
            opacity=0.15
        ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                color="#8a8d9a",
                gridcolor="#2d3142"
            ),
            angularaxis=dict(
                color="#8a8d9a",
                gridcolor="#2d3142"
            ),
            bgcolor="rgba(0,0,0,0)"
        ),
        showlegend=True,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#8a8d9a"),
        margin=dict(l=60, r=60, t=40, b=40)
    )

    st.plotly_chart(fig, width="stretch")


@st.cache_data(show_spinner=False, ttl=600)
def _aggregate_revenue_per_contract(fat_df: pd.DataFrame, partner_captador_map: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates faturamento divided by total contract counts by captador.

    Args:
        fat_df (pd.DataFrame): The filtered faturamento DataFrame.
        partner_captador_map (pd.DataFrame): Mapping of partner to captador.

    Returns:
        pd.DataFrame: Aggregated DataFrame with faturamento per contract by captador.
    """
    if fat_df.empty:
        return pd.DataFrame(columns=[C.UI_LABEL_CAPTADOR_COLUMN, C.UI_LABEL_REVENUE_PER_CONTRACT_COLUMN])

    df_fat = fat_df.copy()
    df_fat[C.COL_INT_PARTNER] = df_fat[C.COL_INT_PARTNER].astype(str).str.strip()
    df_fat = df_fat[df_fat[C.COL_INT_PARTNER] != ""]

    fat_captador_map = _get_faturamento_captador_map(df_fat, partner_captador_map)
    df_fat["Captador"] = df_fat[C.COL_INT_PARTNER].map(fat_captador_map)
    df_fat["Captador"] = df_fat["Captador"].apply(_format_captador_name)

    # Aggregate total faturamento and number of contracts
    df_grouped = df_fat.groupby("Captador").agg(
        total_faturamento=(C.COL_INT_VALOR, "sum"),
        total_contratos=(C.COL_INT_VALOR, "count")
    ).reset_index()

    # Calculate average faturamento per contract
    df_grouped[C.UI_LABEL_REVENUE_PER_CONTRACT_COLUMN] = df_grouped["total_faturamento"] / df_grouped["total_contratos"]

    # Sort descending
    df_grouped = df_grouped.sort_values(by=C.UI_LABEL_REVENUE_PER_CONTRACT_COLUMN, ascending=False)

    df_result = df_grouped[["Captador", C.UI_LABEL_REVENUE_PER_CONTRACT_COLUMN]].copy()
    df_result.columns = [C.UI_LABEL_CAPTADOR_COLUMN, C.UI_LABEL_REVENUE_PER_CONTRACT_COLUMN]

    return df_result


def _render_revenue_per_contract_chart(df: pd.DataFrame) -> None:
    """
    Renders a bar chart showing the average faturamento per contract for each captador.

    Args:
        df (pd.DataFrame): Aggregated DataFrame with faturamento per contract by captador.
    """
    if df.empty:
        st.info(C.UI_LABEL_NO_DATA_PERIOD)
        return

    fig = px.bar(
        df,
        x=C.UI_LABEL_CAPTADOR_COLUMN,
        y=C.UI_LABEL_REVENUE_PER_CONTRACT_COLUMN,
        title=C.UI_LABEL_CAPTADORES_REV_CONTRACT_TITLE,
        labels={
            C.UI_LABEL_CAPTADOR_COLUMN: C.UI_LABEL_CAPTADOR_COLUMN,
            C.UI_LABEL_REVENUE_PER_CONTRACT_COLUMN: C.UI_LABEL_REVENUE_PER_CONTRACT,
        },
        color=C.UI_LABEL_REVENUE_PER_CONTRACT_COLUMN,
        color_continuous_scale=px.colors.sequential.Pinkyl,
        text_auto=".2f",
    )
    fig.update_layout(
        xaxis_tickangle=-45,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#8a8d9a"),
        coloraxis_showscale=False
    )
    st.plotly_chart(fig, width="stretch")


@st.cache_data(show_spinner=False, ttl=600)
def _aggregate_monthly_partners(dados_filtered: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates unique partners captured by month and captador.

    Args:
        dados_filtered (pd.DataFrame): Filtered dados DataFrame.

    Returns:
        pd.DataFrame: Aggregated DataFrame with monthly partners count.
    """
    MAIN_CAPTADORES = ["Leila", "Thais", "Ana Beatriz", "Fernanda", "Lorena Oliveira", "Luiza Martins"]
    if dados_filtered.empty or C.COL_INT_DT not in dados_filtered.columns or C.COL_INT_CAPTADOR not in dados_filtered.columns:
        return pd.DataFrame(columns=["Mês", "Captador", "Parceiros Captados"])

    # Filter to ASSINADO and drop null dates
    df_signed = dados_filtered.dropna(subset=[C.COL_INT_DT, C.COL_INT_CAPTADOR, C.COL_INT_PARTNER])
    df_signed = df_signed[
        (df_signed[C.COL_INT_STATUS].astype(str).str.strip() == C.STATUS_ASSINADO) &
        (df_signed[C.COL_INT_PARTNER].astype(str).str.strip() != "")
    ].copy()

    if df_signed.empty:
        return pd.DataFrame(columns=["Mês", "Captador", "Parceiros Captados"])

    # Clean name
    df_signed["Captador"] = df_signed[C.COL_INT_CAPTADOR].apply(_format_captador_name)
    df_signed = df_signed[df_signed["Captador"].isin(MAIN_CAPTADORES)]

    if df_signed.empty:
        return pd.DataFrame(columns=["Mês", "Captador", "Parceiros Captados"])

    # Extract month
    df_signed["Mês"] = df_signed[C.COL_INT_DT].dt.to_period("M").astype(str)

    # Group
    df_grouped = df_signed.groupby(["Mês", "Captador"])[C.COL_INT_PARTNER].nunique().reset_index(name="Parceiros Captados")

    # Generate complete Cartesian product for months and main captadores to fillna with 0
    months = sorted(df_signed["Mês"].unique())
    idx = pd.MultiIndex.from_product([months, MAIN_CAPTADORES], names=["Mês", "Captador"])
    df_grouped = df_grouped.set_index(["Mês", "Captador"]).reindex(idx, fill_value=0).reset_index()

    # Sort
    df_grouped = df_grouped.sort_values(by=["Mês", "Captador"])
    return df_grouped


@st.cache_data(show_spinner=False, ttl=600)
def _aggregate_cumulative_revenue(fat_filtered: pd.DataFrame, partner_captador_map: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates daily cumulative faturamento over time by captador.

    Args:
        fat_filtered (pd.DataFrame): Filtered faturamento DataFrame.
        partner_captador_map (pd.DataFrame): Mapping of partner to captador.

    Returns:
        pd.DataFrame: Aggregated DataFrame with cumulative faturamento.
    """
    MAIN_CAPTADORES = ["Leila", "Thais", "Ana Beatriz", "Fernanda", "Lorena Oliveira", "Luiza Martins"]
    if fat_filtered.empty or C.COL_INT_DATA not in fat_filtered.columns or C.COL_INT_VALOR not in fat_filtered.columns:
        return pd.DataFrame(columns=["Data", "Captador", "Faturamento Acumulado"])

    df_fat = fat_filtered.copy()
    df_fat[C.COL_INT_PARTNER] = df_fat[C.COL_INT_PARTNER].astype(str).str.strip()
    df_fat = df_fat[df_fat[C.COL_INT_PARTNER] != ""]

    fat_captador_map = _get_faturamento_captador_map(df_fat, partner_captador_map)
    df_fat["Captador"] = df_fat[C.COL_INT_PARTNER].map(fat_captador_map)
    df_fat["Captador"] = df_fat["Captador"].apply(_format_captador_name)

    df_merged = df_fat[df_fat["Captador"].isin(MAIN_CAPTADORES)].copy()

    if df_merged.empty:
        return pd.DataFrame(columns=["Data", "Captador", "Faturamento Acumulado"])

    # Convert data column to date (without time)
    df_merged["Data"] = pd.to_datetime(df_merged[C.COL_INT_DATA]).dt.date

    # Group by Date and Captador
    daily_grouped = df_merged.groupby(["Data", "Captador"])[C.COL_INT_VALOR].sum().reset_index(name="Valor")

    # Reindex to ensure all dates are present for each of the 6 captadores (cumsum carried forward)
    all_dates = pd.date_range(start=df_merged["Data"].min(), end=df_merged["Data"].max(), freq="D").date
    if len(all_dates) == 0:
        all_dates = [df_merged["Data"].min()]

    idx = pd.MultiIndex.from_product([all_dates, MAIN_CAPTADORES], names=["Data", "Captador"])
    daily_full = daily_grouped.set_index(["Data", "Captador"]).reindex(idx, fill_value=0.0).reset_index()
    daily_full = daily_full.sort_values(by=["Data", "Captador"])

    # Cumulative sum per captador group
    daily_full["Faturamento Acumulado"] = daily_full.groupby("Captador")["Valor"].cumsum()

    return daily_full


def _render_monthly_partners_chart(df: pd.DataFrame) -> None:
    """
    Renders a line chart showing unique partners captured by month for each captador.

    Args:
        df (pd.DataFrame): Aggregated DataFrame with monthly partners.
    """
    if df.empty:
        st.info(C.UI_LABEL_NO_DATA_PERIOD)
        return

    colors_list = ["#ff2d95", "#2d9fff", "#00ff7f", "#ffaa00", "#9b5de5", "#f15bb5"]
    fig = px.line(
        df,
        x="Mês",
        y="Parceiros Captados",
        color="Captador",
        color_discrete_sequence=colors_list,
        title=C.UI_LABEL_CAPTADORES_MONTHLY_TITLE,
        labels={
            "Mês": "Mês",
            "Parceiros Captados": "Novos Parceiros",
            "Captador": C.UI_LABEL_CAPTADOR_COLUMN
        },
        markers=True
    )
    fig.update_layout(
        xaxis_tickangle=-45,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#8a8d9a")
    )
    st.plotly_chart(fig, width="stretch")


def _render_cumulative_revenue_chart(df: pd.DataFrame) -> None:
    """
    Renders a line chart showing cumulative faturamento over time for each captador.

    Args:
        df (pd.DataFrame): Aggregated DataFrame with cumulative faturamento.
    """
    if df.empty:
        st.info(C.UI_LABEL_NO_DATA_PERIOD)
        return

    colors_list = ["#ff2d95", "#2d9fff", "#00ff7f", "#ffaa00", "#9b5de5", "#f15bb5"]
    fig = px.line(
        df,
        x="Data",
        y="Faturamento Acumulado",
        color="Captador",
        color_discrete_sequence=colors_list,
        title=C.UI_LABEL_CAPTADORES_CUMSUM_TITLE,
        labels={
            "Data": "Data",
            "Faturamento Acumulado": "Faturamento Acumulado (R$)",
            "Captador": C.UI_LABEL_CAPTADOR_COLUMN
        }
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#8a8d9a")
    )
    st.plotly_chart(fig, width="stretch")


@st.cache_data(show_spinner=False, ttl=600)
def _aggregate_bump_chart_data(fat_filtered: pd.DataFrame, partner_captador_map: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates faturamento by month and captador, then ranks them for a bump chart.
    """
    MAIN_CAPTADORES = ["Leila", "Thais", "Ana Beatriz", "Fernanda", "Lorena Oliveira", "Luiza Martins"]
    if fat_filtered.empty or C.COL_INT_DATA not in fat_filtered.columns or C.COL_INT_VALOR not in fat_filtered.columns:
        return pd.DataFrame(columns=["_ano", "_mes", "Mês Extenso", "Captador", "Faturamento", "rank"])

    df_fat = fat_filtered.copy()
    df_fat[C.COL_INT_PARTNER] = df_fat[C.COL_INT_PARTNER].astype(str).str.strip()
    df_fat = df_fat[df_fat[C.COL_INT_PARTNER] != ""]

    fat_captador_map = _get_faturamento_captador_map(df_fat, partner_captador_map)
    df_fat["Captador"] = df_fat[C.COL_INT_PARTNER].map(fat_captador_map)
    df_fat["Captador"] = df_fat["Captador"].apply(_format_captador_name)

    df_merged = df_fat[df_fat["Captador"].isin(MAIN_CAPTADORES)].copy()

    if df_merged.empty:
        return pd.DataFrame(columns=["_ano", "_mes", "Mês Extenso", "Captador", "Faturamento", "rank"])

    # Convert to datetime and extract year, month
    df_merged["_dt_data"] = pd.to_datetime(df_merged[C.COL_INT_DATA])
    df_merged["_ano"] = df_merged["_dt_data"].dt.year
    df_merged["_mes"] = df_merged["_dt_data"].dt.month

    # Group by year, month, and captador
    monthly_rev = df_merged.groupby(["_ano", "_mes", "Captador"])[C.COL_INT_VALOR].sum().reset_index(name="Faturamento")

    # Generate complete Cartesian product for months and main captadores to fillna with 0 faturamento
    months_years = monthly_rev[["_ano", "_mes"]].drop_duplicates()
    
    records = []
    for _, my in months_years.iterrows():
        for cap in MAIN_CAPTADORES:
            records.append({"_ano": my["_ano"], "_mes": my["_mes"], "Captador": cap})
    idx_df = pd.DataFrame(records)

    # Merge and fillna 0.0
    monthly_rev = pd.merge(idx_df, monthly_rev, on=["_ano", "_mes", "Captador"], how="left").fillna(0.0)

    # Rank monthly
    monthly_rev["rank"] = monthly_rev.groupby(["_ano", "_mes"])["Faturamento"].rank(
        method="min", ascending=False
    ).astype(int)

    # Format month name
    monthly_rev["Mês Extenso"] = monthly_rev.apply(
        lambda r: f"{C.MONTH_NAMES.get(int(r['_mes']), str(int(r['_mes'])))} {int(r['_ano'])}",
        axis=1
    )

    # Sort
    monthly_rev = monthly_rev.sort_values(by=["_ano", "_mes", "Captador"])
    return monthly_rev


def _render_bump_chart(df: pd.DataFrame) -> None:
    """
    Renders a bump chart showing the monthly ranking of captadores by faturamento.
    """
    if df.empty:
        st.info(C.UI_LABEL_NO_DATA_PERIOD)
        return

    # Extract month order sorted chronologically
    month_order = (
        df[["_ano", "_mes", "Mês Extenso"]]
        .drop_duplicates()
        .sort_values(["_ano", "_mes"])["Mês Extenso"]
        .tolist()
    )

    colors_list = ["#ff2d95", "#2d9fff", "#00ff7f", "#ffaa00", "#9b5de5", "#f15bb5"]
    fig = px.line(
        df,
        x="Mês Extenso",
        y="rank",
        color="Captador",
        color_discrete_sequence=colors_list,
        markers=True,
        title=C.UI_LABEL_CAPTADORES_BUMP_TITLE,
        category_orders={"Mês Extenso": month_order},
        labels={
            "Mês Extenso": "Mês",
            "rank": "Rank",
            "Captador": C.UI_LABEL_CAPTADOR_COLUMN
        }
    )
    fig.update_yaxes(autorange="reversed", dtick=1, title="Rank")
    fig.update_xaxes(title="")
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#8a8d9a")
    )
    st.plotly_chart(fig, width="stretch")


@st.cache_data(show_spinner=False, ttl=600)
def _aggregate_heatmap_data(
    dados_filtered: pd.DataFrame,
    fat_filtered: pd.DataFrame,
    raw_dados: pd.DataFrame,
    metric: str
) -> pd.DataFrame:
    """
    Prepares heatmap data: index=Captador, columns=Mês Extenso, values=metric.
    """
    MAIN_CAPTADORES = ["Leila", "Thais", "Ana Beatriz", "Fernanda", "Lorena Oliveira", "Luiza Martins"]

    if metric == "Faturamento":
        partner_map = _aggregate_partner_captador_map(raw_dados)
        df_fat = fat_filtered.copy()
        df_fat[C.COL_INT_PARTNER] = df_fat[C.COL_INT_PARTNER].astype(str).str.strip()
        df_fat = df_fat[df_fat[C.COL_INT_PARTNER] != ""]
        
        fat_captador_map = _get_faturamento_captador_map(df_fat, partner_map)
        df_fat["Captador"] = df_fat[C.COL_INT_PARTNER].map(fat_captador_map)
        df_fat["Captador"] = df_fat["Captador"].apply(_format_captador_name)
        df_merged = df_fat[df_fat["Captador"].isin(MAIN_CAPTADORES)].copy()

        if df_merged.empty:
            return pd.DataFrame()

        df_merged["_dt_data"] = pd.to_datetime(df_merged[C.COL_INT_DATA])
        df_merged["_ano"] = df_merged["_dt_data"].dt.year
        df_merged["_mes"] = df_merged["_dt_data"].dt.month

        monthly = df_merged.groupby(["_ano", "_mes", "Captador"])[C.COL_INT_VALOR].sum().reset_index(name="Value")

    else:  # Parceiros Captados
        if dados_filtered.empty or C.COL_INT_DT not in dados_filtered.columns or C.COL_INT_CAPTADOR not in dados_filtered.columns:
            return pd.DataFrame()

        df_signed = dados_filtered.dropna(subset=[C.COL_INT_DT, C.COL_INT_CAPTADOR, C.COL_INT_PARTNER])
        df_signed = df_signed[df_signed[C.COL_INT_STATUS].astype(str).str.strip() == C.STATUS_ASSINADO].copy()
        df_signed["Captador"] = df_signed[C.COL_INT_CAPTADOR].apply(_format_captador_name)
        df_signed = df_signed[df_signed["Captador"].isin(MAIN_CAPTADORES)]

        if df_signed.empty:
            return pd.DataFrame()

        df_signed["_ano"] = df_signed[C.COL_INT_DT].dt.year
        df_signed["_mes"] = df_signed[C.COL_INT_DT].dt.month

        monthly = df_signed.groupby(["_ano", "_mes", "Captador"])[C.COL_INT_PARTNER].nunique().reset_index(name="Value")

    if monthly.empty:
        return pd.DataFrame()

    months_years = monthly[["_ano", "_mes"]].drop_duplicates().sort_values(["_ano", "_mes"])

    records = []
    for _, my in months_years.iterrows():
        for cap in MAIN_CAPTADORES:
            records.append({"_ano": my["_ano"], "_mes": my["_mes"], "Captador": cap})
    idx_df = pd.DataFrame(records)

    monthly_full = pd.merge(idx_df, monthly, on=["_ano", "_mes", "Captador"], how="left").fillna(0.0)

    monthly_full["Mês Extenso"] = monthly_full.apply(
        lambda r: f"{C.MONTH_NAMES.get(int(r['_mes']), str(int(r['_mes'])))} {int(r['_ano'])}",
        axis=1
    )

    month_order = (
        monthly_full[["_ano", "_mes", "Mês Extenso"]]
        .drop_duplicates()
        .sort_values(["_ano", "_mes"])["Mês Extenso"]
        .tolist()
    )

    pivot_df = monthly_full.pivot(index="Captador", columns="Mês Extenso", values="Value")
    pivot_df = pivot_df.reindex(columns=month_order).fillna(0.0)

    return pivot_df


def _render_heatmap_chart(df: pd.DataFrame, metric: str) -> None:
    """
    Renders a heatmap month x captador with selected metric intensity.
    """
    if df.empty:
        st.info(C.UI_LABEL_NO_DATA_PERIOD)
        return

    fig = px.imshow(
        df,
        labels=dict(x="Mês", y="Captador", color=metric),
        x=df.columns,
        y=df.index,
        color_continuous_scale="Viridis",
        text_auto=".2f" if metric == "Faturamento" else True,
        title=f"{C.UI_LABEL_CAPTADORES_HEATMAP_TITLE} ({metric})"
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#8a8d9a")
    )
    st.plotly_chart(fig, width="stretch")


def _render_stacked_area_chart(df: pd.DataFrame) -> None:
    """
    Renders a stacked area chart showing the composition of monthly faturamento by captador.
    """
    if df.empty:
        st.info(C.UI_LABEL_NO_DATA_PERIOD)
        return

    # Extract month order sorted chronologically
    month_order = (
        df[["_ano", "_mes", "Mês Extenso"]]
        .drop_duplicates()
        .sort_values(["_ano", "_mes"])["Mês Extenso"]
        .tolist()
    )

    colors_list = ["#ff2d95", "#2d9fff", "#00ff7f", "#ffaa00", "#9b5de5", "#f15bb5"]
    fig = px.area(
        df,
        x="Mês Extenso",
        y="Faturamento",
        color="Captador",
        color_discrete_sequence=colors_list,
        title=C.UI_LABEL_CAPTADORES_AREA_TITLE,
        category_orders={"Mês Extenso": month_order},
        labels={
            "Mês Extenso": "Mês",
            "Faturamento": "Faturamento (R$)",
            "Captador": C.UI_LABEL_CAPTADOR_COLUMN
        }
    )
    fig.update_layout(
        xaxis_tickangle=-45,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#8a8d9a")
    )
    st.plotly_chart(fig, width="stretch")


def _aggregate_mom_growth(monthly_rev: pd.DataFrame) -> pd.DataFrame:
    """
    Computes MoM growth rate per captador.
    """
    if monthly_rev.empty:
        return pd.DataFrame(columns=["_ano", "_mes", "Mês Extenso", "Captador", "Crescimento MoM (%)"])

    df = monthly_rev.copy().sort_values(by=["Captador", "_ano", "_mes"])
    df["Crescimento MoM (%)"] = df.groupby("Captador")["Faturamento"].pct_change() * 100.0
    df["Crescimento MoM (%)"] = df["Crescimento MoM (%)"].fillna(0.0).replace([np.inf, -np.inf], 100.0)

    return df


def _render_mom_growth_chart(df: pd.DataFrame) -> None:
    """
    Renders a line chart showing the MoM growth rate per captador.
    """
    if df.empty:
        st.info(C.UI_LABEL_NO_DATA_PERIOD)
        return

    # Extract month order sorted chronologically
    month_order = (
        df[["_ano", "_mes", "Mês Extenso"]]
        .drop_duplicates()
        .sort_values(["_ano", "_mes"])["Mês Extenso"]
        .tolist()
    )

    colors_list = ["#ff2d95", "#2d9fff", "#00ff7f", "#ffaa00", "#9b5de5", "#f15bb5"]
    fig = px.line(
        df,
        x="Mês Extenso",
        y="Crescimento MoM (%)",
        color="Captador",
        color_discrete_sequence=colors_list,
        markers=True,
        title=C.UI_LABEL_CAPTADORES_MOM_TITLE,
        category_orders={"Mês Extenso": month_order},
        labels={
            "Mês Extenso": "Mês",
            "Crescimento MoM (%)": "Crescimento MoM (%)",
            "Captador": C.UI_LABEL_CAPTADOR_COLUMN
        }
    )
    fig.update_layout(
        xaxis_tickangle=-45,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#8a8d9a")
    )
    st.plotly_chart(fig, width="stretch")


def _render_geo_treemap_chart(dados_df: pd.DataFrame) -> None:
    """
    Renders a treemap showing Região -> Estado -> Captador based on unique signed partners.
    """
    MAIN_CAPTADORES = ["Leila", "Thais", "Ana Beatriz", "Fernanda", "Lorena Oliveira", "Luiza Martins"]
    if dados_df.empty:
        st.info(C.UI_LABEL_NO_DATA_PERIOD)
        return

    # Filter signed contracts
    df_tree = dados_df.dropna(subset=[C.COL_INT_REGION, C.COL_INT_STATE, C.COL_INT_CAPTADOR, C.COL_INT_PARTNER]).copy()
    df_tree = df_tree[
        (df_tree[C.COL_INT_STATUS].astype(str).str.strip() == C.STATUS_ASSINADO) &
        (df_tree[C.COL_INT_PARTNER].astype(str).str.strip() != "")
    ]
    df_tree["Captador"] = df_tree[C.COL_INT_CAPTADOR].apply(_format_captador_name)
    df_tree = df_tree[df_tree["Captador"].isin(MAIN_CAPTADORES)]

    if df_tree.empty:
        st.info(C.UI_LABEL_NO_DATA_PERIOD)
        return

    g = (
        df_tree.groupby([C.COL_INT_REGION, C.COL_INT_STATE, "Captador"])[C.COL_INT_PARTNER]
        .nunique()
        .reset_index(name="Parceiros")
    )

    if g.empty:
        st.info(C.UI_LABEL_NO_DATA_PERIOD)
        return

    fig = px.treemap(
        g,
        path=[C.COL_INT_REGION, C.COL_INT_STATE, "Captador"],
        values="Parceiros",
        color="Parceiros",
        color_continuous_scale="Blues",
        title=C.UI_LABEL_CAPTADORES_TREEMAP_TITLE
    )
    fig.update_traces(textinfo="label+value")
    st.plotly_chart(fig, width="stretch")


def _render_geo_state_heatmap(dados_df: pd.DataFrame) -> None:
    """
    Renders a heatmap showing the number of partners by Estado (Y) and Captador (X).
    """
    MAIN_CAPTADORES = ["Leila", "Thais", "Ana Beatriz", "Fernanda", "Lorena Oliveira", "Luiza Martins"]
    if dados_df.empty:
        st.info(C.UI_LABEL_NO_DATA_PERIOD)
        return

    df_signed = dados_df.dropna(subset=[C.COL_INT_STATE, C.COL_INT_CAPTADOR, C.COL_INT_PARTNER]).copy()
    df_signed = df_signed[
        (df_signed[C.COL_INT_STATUS].astype(str).str.strip() == C.STATUS_ASSINADO) &
        (df_signed[C.COL_INT_PARTNER].astype(str).str.strip() != "")
    ]
    df_signed["Captador"] = df_signed[C.COL_INT_CAPTADOR].apply(_format_captador_name)
    df_signed = df_signed[df_signed["Captador"].isin(MAIN_CAPTADORES)]

    if df_signed.empty:
        st.info(C.UI_LABEL_NO_DATA_PERIOD)
        return

    g = (
        df_signed.groupby([C.COL_INT_STATE, "Captador"])[C.COL_INT_PARTNER]
        .nunique()
        .reset_index(name="Parceiros")
    )

    # Pivot: index=Estado, columns=Captador, values=Parceiros
    pivot_df = g.pivot(index=C.COL_INT_STATE, columns="Captador", values="Parceiros").fillna(0.0)

    # Sort index (states alphabetically)
    pivot_df = pivot_df.sort_index()

    fig = px.imshow(
        pivot_df,
        labels=dict(x="Captador", y="Estado (UF)", color="Parceiros"),
        x=pivot_df.columns,
        y=pivot_df.index,
        color_continuous_scale="Viridis",
        text_auto=True,
        title=C.UI_LABEL_CAPTADORES_HEATMAP_STATE_TITLE
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#8a8d9a")
    )
    st.plotly_chart(fig, width="stretch")


def _render_regional_stacked_bar(dados_df: pd.DataFrame) -> None:
    """
    Renders a stacked bar chart of Captador vs Região showing how regionalized they are.
    """
    MAIN_CAPTADORES = ["Leila", "Thais", "Ana Beatriz", "Fernanda", "Lorena Oliveira", "Luiza Martins"]
    if dados_df.empty:
        st.info(C.UI_LABEL_NO_DATA_PERIOD)
        return

    df_signed = dados_df.dropna(subset=[C.COL_INT_REGION, C.COL_INT_CAPTADOR, C.COL_INT_PARTNER]).copy()
    df_signed = df_signed[
        (df_signed[C.COL_INT_STATUS].astype(str).str.strip() == C.STATUS_ASSINADO) &
        (df_signed[C.COL_INT_PARTNER].astype(str).str.strip() != "")
    ]
    df_signed["Captador"] = df_signed[C.COL_INT_CAPTADOR].apply(_format_captador_name)
    df_signed = df_signed[df_signed["Captador"].isin(MAIN_CAPTADORES)]

    if df_signed.empty:
        st.info(C.UI_LABEL_NO_DATA_PERIOD)
        return

    g = (
        df_signed.groupby(["Captador", C.COL_INT_REGION])[C.COL_INT_PARTNER]
        .nunique()
        .reset_index(name="Parceiros")
    )

    colors_list = ["#ff2d95", "#2d9fff", "#00ff7f", "#ffaa00", "#9b5de5", "#f15bb5"]
    fig = px.bar(
        g,
        x="Captador",
        y="Parceiros",
        color=C.COL_INT_REGION,
        color_discrete_sequence=colors_list,
        title=C.UI_LABEL_CAPTADORES_BAR_REG_TITLE,
        barmode="stack",
        labels={
            "Captador": "Captador",
            "Parceiros": "Novos Parceiros",
            C.COL_INT_REGION: "Região"
        }
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#8a8d9a")
    )
    st.plotly_chart(fig, width="stretch")


@st.cache_data(show_spinner=False, ttl=600)
def _aggregate_geo_dispersion(dados_filtered: pd.DataFrame) -> pd.DataFrame:
    """
    Computes geographic dispersion metrics (unique states, unique cities, HHI) by captador.
    """
    MAIN_CAPTADORES = ["Leila", "Thais", "Ana Beatriz", "Fernanda", "Lorena Oliveira", "Luiza Martins"]
    if dados_filtered.empty:
        return pd.DataFrame(columns=["Captador", "Estados Atingidos", "Cidades Atingidas", "HHI Regional"])

    # Filter to signed contracts
    df_signed = dados_filtered.dropna(subset=[C.COL_INT_CAPTADOR, C.COL_INT_STATE, C.COL_INT_CITY]).copy()
    df_signed = df_signed[df_signed[C.COL_INT_STATUS].astype(str).str.strip() == C.STATUS_ASSINADO]
    df_signed["Captador"] = df_signed[C.COL_INT_CAPTADOR].apply(_format_captador_name)
    df_signed = df_signed[df_signed["Captador"].isin(MAIN_CAPTADORES)]

    if df_signed.empty:
        return pd.DataFrame(columns=["Captador", "Estados Atingidos", "Cidades Atingidas", "HHI Regional"])

    records = []
    for cap in MAIN_CAPTADORES:
        df_cap = df_signed[df_signed["Captador"] == cap]
        if df_cap.empty:
            records.append({
                "Captador": cap,
                "Estados Atingidos": 0,
                "Cidades Atingidas": 0,
                "HHI Regional": 0.0
            })
            continue

        states_count = df_cap[C.COL_INT_STATE].nunique()
        cities_count = df_cap[C.COL_INT_CITY].nunique()

        # Compute HHI for state distribution
        state_shares = df_cap[C.COL_INT_STATE].value_counts(normalize=True)
        hhi = (state_shares ** 2).sum() * 10000.0

        records.append({
            "Captador": cap,
            "Estados Atingidos": states_count,
            "Cidades Atingidas": cities_count,
            "HHI Regional": round(hhi, 1)
        })

    return pd.DataFrame(records)


def _calculate_captador_commission_projection(fat_filtered: pd.DataFrame, partner_map: pd.DataFrame, captador_pct: float) -> pd.DataFrame:
    """
    Projects the current month faturamento and commission for each of the 6 main captadores.
    """
    MAIN_CAPTADORES = ["Leila", "Thais", "Ana Beatriz", "Fernanda", "Lorena Oliveira", "Luiza Martins"]
    if fat_filtered.empty or C.COL_INT_DATA not in fat_filtered.columns or C.COL_INT_VALOR not in fat_filtered.columns:
        return pd.DataFrame()

    df_fat = fat_filtered.copy()
    df_fat["Data_parsed"] = pd.to_datetime(df_fat[C.COL_INT_DATA])
    max_date = df_fat["Data_parsed"].max()
    if pd.isna(max_date):
        return pd.DataFrame()

    current_year = max_date.year
    current_month = max_date.month
    
    # Filter to current month
    df_month = df_fat[(df_fat["Data_parsed"].dt.year == current_year) & (df_fat["Data_parsed"].dt.month == current_month)].copy()
    
    # Elapsed days and total days in month
    elapsed_days = max_date.day
    total_days = max_date.days_in_month
    remaining_days = total_days - elapsed_days

    # Map to captador
    df_month[C.COL_INT_PARTNER] = df_month[C.COL_INT_PARTNER].astype(str).str.strip()
    df_month = df_month[df_month[C.COL_INT_PARTNER] != ""]
    
    fat_captador_map = _get_faturamento_captador_map(df_month, partner_map)
    df_month["Captador"] = df_month[C.COL_INT_PARTNER].map(fat_captador_map)
    df_month["Captador"] = df_month["Captador"].apply(_format_captador_name)

    records = []
    for cap in MAIN_CAPTADORES:
        cap_df = df_month[df_month["Captador"] == cap]
        realizado = cap_df[C.COL_INT_VALOR].sum() if not cap_df.empty else 0.0
        
        # Calculate forecast using run-rate (ritmo atual)
        daily_rate = realizado / elapsed_days if elapsed_days > 0 else 0.0
        projection = realizado + (daily_rate * remaining_days)
        
        comissao_realizada = realizado * (captador_pct / 100.0)
        comissao_projetada = projection * (captador_pct / 100.0)
        
        records.append({
            "Captador": cap,
            "Realizado (R$)": round(realizado, 2),
            "Comissão Realizada (R$)": round(comissao_realizada, 2),
            "Projetado (R$)": round(projection, 2),
            "Comissão Projetada (R$)": round(comissao_projetada, 2),
            "Progresso (%)": round((realizado / projection * 100.0), 1) if projection > 0 else 0.0
        })
    return pd.DataFrame(records)


def _render_captador_commission_projection(df: pd.DataFrame) -> None:
    """
    Renders a bar chart comparing current month realized vs projected commission per captador.
    """
    if df.empty:
        st.info(C.UI_LABEL_NO_DATA_PERIOD)
        return

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["Captador"],
        y=df["Comissão Realizada (R$)"],
        name="Realizada no Mês",
        marker_color="#ff2d95"
    ))
    fig.add_trace(go.Bar(
        x=df["Captador"],
        y=df["Comissão Projetada (R$)"],
        name="Projetada (Ritmo Atual)",
        marker_color="#2d9fff"
    ))
    fig.update_layout(
        barmode="group",
        title=C.UI_LABEL_CAPTADORES_PROJ_TITLE,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#8a8d9a"),
        yaxis=dict(title="Comissão (R$)")
    )
    st.plotly_chart(fig, width="stretch")


def _render_revenue_waterfall(fat_filtered: pd.DataFrame, partner_map: pd.DataFrame) -> None:
    """
    Renders a waterfall chart of faturamento contribution by captador.
    """
    MAIN_CAPTADORES = ["Leila", "Thais", "Ana Beatriz", "Fernanda", "Lorena Oliveira", "Luiza Martins"]
    if fat_filtered.empty or C.COL_INT_VALOR not in fat_filtered.columns:
        st.info(C.UI_LABEL_NO_DATA_PERIOD)
        return

    df_fat = fat_filtered.copy()
    df_fat[C.COL_INT_PARTNER] = df_fat[C.COL_INT_PARTNER].astype(str).str.strip()
    df_fat = df_fat[df_fat[C.COL_INT_PARTNER] != ""]
    
    fat_captador_map = _get_faturamento_captador_map(df_fat, partner_map)
    df_fat["Captador"] = df_fat[C.COL_INT_PARTNER].map(fat_captador_map)
    df_fat["Captador"] = df_fat["Captador"].apply(_format_captador_name)

    sums = {}
    for cap in MAIN_CAPTADORES:
        sums[cap] = df_fat[df_fat["Captador"] == cap][C.COL_INT_VALOR].sum()

    unidentified = df_fat[~df_fat["Captador"].isin(MAIN_CAPTADORES)][C.COL_INT_VALOR].sum()
    
    x_labels = list(sums.keys())
    y_values = list(sums.values())
    measure = ["relative"] * len(x_labels)

    if unidentified > 0:
        x_labels.append("Outros")
        y_values.append(unidentified)
        measure.append("relative")

    x_labels.append("Total")
    y_values.append(sum(y_values))
    measure.append("total")

    fig = go.Figure(go.Waterfall(
        name="Contribuição",
        orientation="v",
        measure=measure,
        x=x_labels,
        textposition="outside",
        text=[f"R$ {v:,.2f}" for v in y_values],
        y=y_values,
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        decreasing={"marker": {"color": "#ff2d95"}},
        increasing={"marker": {"color": "#00ff7f"}},
        totals={"marker": {"color": "#2d9fff"}}
    ))

    fig.update_layout(
        title=C.UI_LABEL_CAPTADORES_WATERFALL_TITLE,
        showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#8a8d9a")
    )
    st.plotly_chart(fig, width="stretch")


@st.cache_data(show_spinner=False, ttl=600)
def _aggregate_seasonality(dados_filtered: pd.DataFrame, freq: str) -> pd.DataFrame:
    """
    Aggregates signed partners by calendar month or quarter to analyze seasonality.
    """
    MAIN_CAPTADORES = ["Leila", "Thais", "Ana Beatriz", "Fernanda", "Lorena Oliveira", "Luiza Martins"]
    if dados_filtered.empty or C.COL_INT_DT not in dados_filtered.columns or C.COL_INT_CAPTADOR not in dados_filtered.columns:
        return pd.DataFrame()

    df_signed = dados_filtered.dropna(subset=[C.COL_INT_DT, C.COL_INT_CAPTADOR, C.COL_INT_PARTNER]).copy()
    df_signed = df_signed[df_signed[C.COL_INT_STATUS].astype(str).str.strip() == C.STATUS_ASSINADO]
    df_signed["Captador"] = df_signed[C.COL_INT_CAPTADOR].apply(_format_captador_name)
    df_signed = df_signed[df_signed["Captador"].isin(MAIN_CAPTADORES)]

    if df_signed.empty:
        return pd.DataFrame()

    if freq == "Mensal":
        df_signed["Periodo"] = df_signed[C.COL_INT_DT].dt.month
        period_names = {1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun", 7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez"}
    else:  # Trimestral
        df_signed["Periodo"] = df_signed[C.COL_INT_DT].dt.quarter
        period_names = {1: "T1", 2: "T2", 3: "T3", 4: "T4"}

    g = df_signed.groupby(["Captador", "Periodo"])[C.COL_INT_PARTNER].nunique().reset_index(name="Parceiros")
    
    all_periods = list(period_names.keys())
    records = []
    for cap in MAIN_CAPTADORES:
        for p in all_periods:
            records.append({"Captador": cap, "Periodo": p})
    idx_df = pd.DataFrame(records)

    g = pd.merge(idx_df, g, on=["Captador", "Periodo"], how="left").fillna(0.0)
    g["Nome Periodo"] = g["Periodo"].map(period_names)
    g = g.sort_values(by=["Captador", "Periodo"])

    return g


def _render_captador_seasonality(df: pd.DataFrame) -> None:
    """
    Renders a line chart displaying seasonality by calendar month or quarter.
    """
    if df.empty:
        st.info(C.UI_LABEL_NO_DATA_PERIOD)
        return

    colors_list = ["#ff2d95", "#2d9fff", "#00ff7f", "#ffaa00", "#9b5de5", "#f15bb5"]
    fig = px.line(
        df,
        x="Nome Periodo",
        y="Parceiros",
        color="Captador",
        color_discrete_sequence=colors_list,
        markers=True,
        title=C.UI_LABEL_CAPTADORES_SEASONALITY_TITLE,
        labels={
            "Nome Periodo": "Período",
            "Parceiros": "Novos Parceiros",
            "Captador": C.UI_LABEL_CAPTADOR_COLUMN
        }
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#8a8d9a")
    )
    st.plotly_chart(fig, width="stretch")


def render(dados_filtered: pd.DataFrame, fat_filtered: pd.DataFrame, raw_dados: pd.DataFrame, access_key: str):
    """
    Renders the Captadores tab with performance metrics and charts.

    Args:
        dados_filtered (pd.DataFrame): Filtered dados DataFrame.
        fat_filtered (pd.DataFrame): Filtered faturamento DataFrame.
        raw_dados (pd.DataFrame): Unfiltered raw dados DataFrame for static mapping.
        access_key (str): Authentication key.
    """
    st.header(C.UI_LABEL_CAPTADORES_TAB_HEADER)

    if not _check_authentication(access_key):
        return

    st.divider()

    # View toggle selector at the top
    view_option = st.radio(
        "Selecione a Análise",
        ["Visão Geral de Performance", "Análise Geográfica"],
        horizontal=True,
        key="captadores_view_select"
    )

    partner_map = _aggregate_partner_captador_map(raw_dados)
    unmatched_list = _get_unmatched_partners(fat_filtered, partner_map)
    overrides = _load_partner_overrides()

    if unmatched_list or overrides:
        with st.expander("🔧 Vincular Parceiros não Identificados", expanded=False):
            st.markdown(
                "Alguns parceiros registrados na aba **Faturamento** não foram encontrados na aba **Dados** ou possuem grafias diferentes. "
                "Associe-os manualmente a um Captador abaixo para atualizar todos os gráficos em tempo real:"
            )
            
            # 1. New assignments
            if unmatched_list:
                st.subheader("Novas Pendências de Vínculo")
                new_assignments = {}
                for partner in unmatched_list:
                    col_p, col_c = st.columns([2, 1])
                    with col_p:
                        st.write(f"• **{partner}**")
                    with col_c:
                        selected_cap = st.selectbox(
                            "Captador",
                            ["Não identificado", "Leila", "Thais", "Ana Beatriz", "Fernanda", "Lorena Oliveira", "Luiza Martins"],
                            key=f"override_select_{partner}"
                        )
                        if selected_cap != "Não identificado":
                            new_assignments[partner] = selected_cap
                
                if new_assignments:
                    if st.button("Salvar Vínculos", key="btn_save_overrides"):
                        overrides.update(new_assignments)
                        _save_partner_overrides(overrides)
                        st.cache_data.clear() # Clear cache so aggregations are recomputed
                        st.success("Vínculos salvos com sucesso!")
                        st.rerun()
            
            # 2. Saved overrides
            if overrides:
                st.subheader("Vínculos Salvos")
                to_delete = []
                for partner, cap in list(overrides.items()):
                    col_p, col_c, col_btn = st.columns([2, 1, 1])
                    with col_p:
                        st.write(f"**{partner}**")
                    with col_c:
                        st.write(f"➔ {cap}")
                    with col_btn:
                        if st.button("Remover", key=f"delete_override_{partner}"):
                            to_delete.append(partner)
                
                if to_delete:
                    for p in to_delete:
                        del overrides[p]
                    _save_partner_overrides(overrides)
                    st.cache_data.clear() # Clear cache so aggregations are recomputed
                    st.success("Vínculo removido com sucesso!")
                    st.rerun()

    st.divider()

    if view_option == "Visão Geral de Performance":
        # 1. Captured partners count (where status is ASSINADO)
        captured_df = _aggregate_captured_partners(dados_filtered)

        # 2. Waiting contracts count (where status is AGUARDANDO)
        waiting_df = _aggregate_waiting_contracts(dados_filtered)

        # 3. Revenue mapping (based on raw_dados partner-captador mapping for static persistence)
        revenue_df = _aggregate_revenue_by_captador(fat_filtered, partner_map)
        ticket_df = _aggregate_ticket_medio_by_captador(fat_filtered, partner_map)
        contract_avg_df = _aggregate_revenue_per_contract(fat_filtered, partner_map)
        monthly_partners_df = _aggregate_monthly_partners(dados_filtered)
        cumulative_rev_df = _aggregate_cumulative_revenue(fat_filtered, partner_map)

        # Aggregations for newer advanced charts
        bump_df = _aggregate_bump_chart_data(fat_filtered, partner_map)
        mom_df = _aggregate_mom_growth(bump_df)

        # KPIs metrics row
        total_captadores = captured_df[C.UI_LABEL_CAPTADOR_COLUMN].nunique()
        total_partners = captured_df[C.UI_LABEL_PARTNERS_CAPTURED_COLUMN].sum() if not captured_df.empty else 0
        total_waiting = waiting_df[C.UI_LABEL_WAITING_CONTRACTS_COLUMN].sum() if not waiting_df.empty else 0
        avg_partners = total_partners / total_captadores if total_captadores > 0 else 0.0

        metrics_html = f"""
        <div style="display: flex; gap: 15px; justify-content: space-between; margin-bottom: 20px; flex-wrap: wrap;">
          <div style="flex: 1; min-width: 150px; background-color: #171b26; padding: 12px; border-radius: 8px; border: 1px solid #2d3142;">
            <div style="font-size: 0.8rem; color: #8a8d9a; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">{C.UI_LABEL_CAPTADORES_ACTIVE}</div>
            <div style="font-size: 1.5rem; font-weight: bold; margin-top: 6px; color: #e2e8f0;">{total_captadores}</div>
          </div>
          <div style="flex: 1; min-width: 150px; background-color: #171b26; padding: 12px; border-radius: 8px; border: 1px solid #2d3142;">
            <div style="font-size: 0.8rem; color: #8a8d9a; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">{C.UI_LABEL_PARTNERS_CAPTURED}</div>
            <div style="font-size: 1.5rem; font-weight: bold; margin-top: 6px; color: #e2e8f0;">{total_partners}</div>
          </div>
          <div style="flex: 1; min-width: 150px; background-color: #171b26; padding: 12px; border-radius: 8px; border: 1px solid #2d3142;">
            <div style="font-size: 0.8rem; color: #8a8d9a; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">{C.UI_LABEL_CAPTADORES_WAITING}</div>
            <div style="font-size: 1.5rem; font-weight: bold; margin-top: 6px; color: #e2e8f0;">{total_waiting}</div>
          </div>
          <div style="flex: 1; min-width: 150px; background-color: #171b26; padding: 12px; border-radius: 8px; border: 1px solid #2d3142;">
            <div style="font-size: 0.8rem; color: #8a8d9a; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">{C.UI_LABEL_AVG_PARTNERS}</div>
            <div style="font-size: 1.5rem; font-weight: bold; margin-top: 6px; color: #e2e8f0;">{avg_partners:.1f}</div>
          </div>
        </div>
        """
        st.markdown(metrics_html, unsafe_allow_html=True)

        # Grid layout: Row 1
        col1, col2 = st.columns(2)
        with col1:
            _render_captured_partners_chart(captured_df)
        with col2:
            _render_waiting_contracts_chart(waiting_df)

        st.divider()

        # Revenue aggregation controls
        exclude_unidentified = st.checkbox(C.UI_LABEL_EXCLUDE_UNIDENTIFIED, value=False)
        if exclude_unidentified:
            if not revenue_df.empty:
                revenue_df = revenue_df[revenue_df[C.UI_LABEL_CAPTADOR_COLUMN] != C.UI_LABEL_UNIDENTIFIED]
            if not ticket_df.empty:
                ticket_df = ticket_df[ticket_df[C.UI_LABEL_CAPTADOR_COLUMN] != C.UI_LABEL_UNIDENTIFIED]
            if not contract_avg_df.empty:
                contract_avg_df = contract_avg_df[contract_avg_df[C.UI_LABEL_CAPTADOR_COLUMN] != C.UI_LABEL_UNIDENTIFIED]

        # Grid layout: Row 2
        col_bottom1, col_bottom2 = st.columns(2)
        with col_bottom1:
            _render_revenue_chart(revenue_df)
        with col_bottom2:
            _render_ticket_medio_chart(ticket_df)

        st.divider()

        # Grid layout: Row 3 (Faturamento por contrato and Radar)
        col_radar1, col_radar2 = st.columns(2)
        with col_radar1:
            _render_revenue_per_contract_chart(contract_avg_df)
        with col_radar2:
            st.subheader(C.UI_LABEL_CAPTADORES_RADAR_TITLE)
            st.markdown(C.UI_LABEL_CAPTADORES_RADAR_DESC)

            global_tax_pct = st.session_state.get("global_tax_pct", 30.0)
            team_categories = st.session_state.get("team_categories", {})
            captador_pct = team_categories.get("captador", {}).get("percentage", 1.6)

            radar_df = _aggregate_radar_data(dados_filtered, fat_filtered, raw_dados, global_tax_pct, captador_pct)
            _render_radar_chart(radar_df)

        st.divider()

        # Grid layout: Row 4 (Timeline Line Charts)
        col_line1, col_line2 = st.columns(2)
        with col_line1:
            _render_monthly_partners_chart(monthly_partners_df)
        with col_line2:
            _render_cumulative_revenue_chart(cumulative_rev_df)

        st.divider()

        # Grid layout: Row 5 (Bump Chart and MoM growth)
        col_row5_1, col_row5_2 = st.columns(2)
        with col_row5_1:
            _render_bump_chart(bump_df)
        with col_row5_2:
            _render_mom_growth_chart(mom_df)

        st.divider()

        # Grid layout: Row 6 (Stacked Area and Heatmap)
        col_row6_1, col_row6_2 = st.columns(2)
        with col_row6_1:
            _render_stacked_area_chart(bump_df)
        with col_row6_2:
            st.subheader(C.UI_LABEL_CAPTADORES_HEATMAP_TITLE)
            st.markdown(C.UI_LABEL_CAPTADORES_HEATMAP_DESC)

            heatmap_metric = st.radio("Métrica do Heatmap", ["Faturamento", "Parceiros Captados"], horizontal=True, key="heatmap_metric_radio")
            heatmap_df = _aggregate_heatmap_data(dados_filtered, fat_filtered, raw_dados, heatmap_metric)
            _render_heatmap_chart(heatmap_df, heatmap_metric)

        st.divider()

        # Grid layout: Row 7 (Projeção de comissão e Waterfall de faturamento)
        col_row7_1, col_row7_2 = st.columns(2)
        with col_row7_1:
            # Commission percentage from session state or default
            team_categories = st.session_state.get("team_categories", {})
            captador_pct = team_categories.get("captador", {}).get("percentage", 1.6)
            proj_df = _calculate_captador_commission_projection(fat_filtered, partner_map, captador_pct)
            _render_captador_commission_projection(proj_df)
        with col_row7_2:
            _render_revenue_waterfall(fat_filtered, partner_map)

        st.divider()

        # Grid layout: Row 8 (Sazonalidade)
        col_row8_1, col_row8_2 = st.columns([3, 1])
        with col_row8_2:
            st.subheader("Sazonalidade")
            st.markdown(C.UI_LABEL_CAPTADORES_SEASONALITY_DESC)
            seas_freq = st.radio(
                "Frequência da Sazonalidade",
                ["Mensal", "Trimestral"],
                horizontal=False,
                key="seasonality_freq_radio"
            )
        with col_row8_1:
            seas_df = _aggregate_seasonality(dados_filtered, seas_freq)
            _render_captador_seasonality(seas_df)

    elif view_option == "Análise Geográfica":
        st.subheader(C.UI_LABEL_CAPTADORES_GEO_HEADER)

        # Compute geo dispersion metrics
        geo_df = _aggregate_geo_dispersion(dados_filtered)

        # Row 1: Treemap and Heatmap Estado x Captador
        col_geo1, col_geo2 = st.columns(2)
        with col_geo1:
            _render_geo_treemap_chart(dados_filtered)
        with col_geo2:
            _render_geo_state_heatmap(dados_filtered)

        st.divider()

        # Row 2: Stacked Bar and Dispersion Table
        col_geo3, col_geo4 = st.columns(2)
        with col_geo3:
            _render_regional_stacked_bar(dados_filtered)
        with col_geo4:
            st.subheader(C.UI_LABEL_CAPTADORES_DISPERSION_TITLE)
            st.markdown(C.UI_LABEL_CAPTADORES_DISPERSION_DESC)
            st.dataframe(geo_df, use_container_width=True, hide_index=True)







