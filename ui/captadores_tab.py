import streamlit as st
import pandas as pd
import plotly.express as px
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


@st.cache_data(show_spinner=False, ttl=600)
def _aggregate_partner_captador_map(dados_df: pd.DataFrame) -> pd.DataFrame:
    """
    Creates a unique mapping between partners and their respective captadores from dados_df.

    Args:
        dados_df (pd.DataFrame): The filtered or raw dados DataFrame.

    Returns:
        pd.DataFrame: A DataFrame with columns [C.COL_INT_PARTNER, C.COL_INT_CAPTADOR].
    """
    if dados_df.empty:
        return pd.DataFrame(columns=[C.COL_INT_PARTNER, C.COL_INT_CAPTADOR])

    # Select partner and captador columns
    df_map = dados_df[[C.COL_INT_PARTNER, C.COL_INT_CAPTADOR]].copy()

    # Drop rows where partner is null or empty
    df_map[C.COL_INT_PARTNER] = df_map[C.COL_INT_PARTNER].astype(str).str.strip()
    df_map = df_map[df_map[C.COL_INT_PARTNER] != ""]

    # Clean captador name (strip)
    df_map[C.COL_INT_CAPTADOR] = df_map[C.COL_INT_CAPTADOR].astype(str).str.strip()

    # Drop duplicates to have unique partner -> captador
    df_map = df_map.drop_duplicates(subset=[C.COL_INT_PARTNER])

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

    # Clean partner names in faturamento
    df_fat = fat_df.copy()
    df_fat[C.COL_INT_PARTNER] = df_fat[C.COL_INT_PARTNER].astype(str).str.strip()
    df_fat = df_fat[df_fat[C.COL_INT_PARTNER] != ""]

    # Merge with partner_captador_map
    df_merged = pd.merge(
        df_fat,
        partner_captador_map,
        on=C.COL_INT_PARTNER,
        how="left"
    )

    # Clean and standardize captador column using mapper
    df_merged[C.COL_INT_CAPTADOR] = df_merged[C.COL_INT_CAPTADOR].apply(_format_captador_name)

    # Aggregate
    df_grouped = df_merged.groupby(C.COL_INT_CAPTADOR).agg(
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


def render(dados_df: pd.DataFrame, fat_df: pd.DataFrame, access_key: str):
    """
    Renders the Captadores tab with performance metrics and charts.

    Args:
        dados_df (pd.DataFrame): Filtered dados DataFrame.
        fat_df (pd.DataFrame): Filtered faturamento DataFrame.
        access_key (str): Authentication key.
    """
    st.header(C.UI_LABEL_CAPTADORES_TAB_HEADER)

    if not _check_authentication(access_key):
        return

    st.divider()

    # 1. Captured partners count (where status is ASSINADO)
    captured_df = _aggregate_captured_partners(dados_df)

    # 2. Waiting contracts count (where status is AGUARDANDO)
    waiting_df = _aggregate_waiting_contracts(dados_df)

    # 3. Revenue mapping (based on dados_df partner-captador mapping)
    partner_map = _aggregate_partner_captador_map(dados_df)
    revenue_df = _aggregate_revenue_by_captador(fat_df, partner_map)

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

    # Grid layout for first two charts
    col1, col2 = st.columns(2)
    with col1:
        _render_captured_partners_chart(captured_df)
    with col2:
        _render_waiting_contracts_chart(waiting_df)

    st.divider()

    # Revenue aggregation controls
    exclude_unidentified = st.checkbox(C.UI_LABEL_EXCLUDE_UNIDENTIFIED, value=False)
    if exclude_unidentified and not revenue_df.empty:
        revenue_df = revenue_df[revenue_df[C.UI_LABEL_CAPTADOR_COLUMN] != C.UI_LABEL_UNIDENTIFIED]

    _render_revenue_chart(revenue_df)
