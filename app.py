import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, date
from dateutil import parser
from io import StringIO
import os
import logging
from dotenv import load_dotenv
import pydeck as pdk
from geocoding_service import GeocodingService
import constants as C

# Setup Logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="Educa Mais Dashboard", layout="wide")
load_dotenv()
DEFAULT_SHEET_ID = os.getenv("DEFAULT_SHEET_ID")
geo_service = GeocodingService()

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------


def parse_datetime_any(s: str) -> datetime | None:
    if pd.isna(s):
        return None
    try:
        return parser.parse(str(s), dayfirst=True)
    except Exception:
        try:
            return parser.parse(str(s), dayfirst=False)
        except Exception:
            return None


def to_float_any(x) -> float:
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

    # Data Processing
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

    # Set Temporal Index for faster filtering
    # We keep '_dt' generic column too but index helps
    if C.COL_INT_DT in df.columns:
        # Ensure datetime type
        df[C.COL_INT_DT] = pd.to_datetime(df[C.COL_INT_DT], errors="coerce")

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

    if C.COL_INT_DATA in df.columns:
        df[C.COL_INT_DATA] = pd.to_datetime(df[C.COL_INT_DATA], errors="coerce")

    return df


# -----------------------------------------------------------------------------
# UI Components
# -----------------------------------------------------------------------------


def gauge_chart(value: float, target: float, title: str) -> go.Figure:
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value,
            title={"text": title},
            gauge={
                "axis": {"range": [0, target]},
                "bar": {"color": C.COLOR_SECONDARY},
                "bgcolor": C.COLOR_BG_DARK,
            },
        )
    )
    fig.update_layout(height=250, margin=dict(l=10, r=10, t=40, b=10))
    return fig


def render_contracts_tab(df: pd.DataFrame, end_date: date, selected_month: int | None):
    col_a, col_b, _, _ = st.columns([1, 1, 1, 1])

    status_counts = df[C.COL_INT_STATUS].value_counts()
    signed_count = int(status_counts.get(C.STATUS_ASSINADO, 0))
    waiting_count = int(status_counts.get(C.STATUS_AGUARDANDO, 0))

    col_a.metric("Contratos assinados", signed_count)
    col_b.metric("Contratos aguardando", waiting_count)

    now = date.today()
    focus_year = end_date.year if isinstance(end_date, date) else now.year
    focus_month = selected_month if selected_month is not None else now.month

    # Filter for signed
    signed_df = df[df[C.COL_INT_STATUS] == C.STATUS_ASSINADO]

    # Monthly
    month_mask = (signed_df[C.COL_INT_DT].dt.year == focus_year) & (
        signed_df[C.COL_INT_DT].dt.month == focus_month
    )
    month_count = signed_df[month_mask].shape[0]

    # Quarterly
    q_start = ((focus_month - 1) // 3) * 3 + 1
    quarterly_mask = (
        (signed_df[C.COL_INT_DT].dt.year == focus_year)
        & (signed_df[C.COL_INT_DT].dt.month >= q_start)
        & (signed_df[C.COL_INT_DT].dt.month <= q_start + 2)
    )
    quarterly_count = signed_df[quarterly_mask].shape[0]

    # Semestral
    sem_start = 1 if focus_month <= 6 else 7
    semestral_mask = (
        (signed_df[C.COL_INT_DT].dt.year == focus_year)
        & (signed_df[C.COL_INT_DT].dt.month >= sem_start)
        & (signed_df[C.COL_INT_DT].dt.month <= sem_start + 5)
    )
    semiannual_count = signed_df[semestral_mask].shape[0]

    g1, g2, g3 = st.columns([1, 1, 1])
    g1.plotly_chart(gauge_chart(month_count, 30, "Meta mensal 30"), width="stretch")
    g2.plotly_chart(
        gauge_chart(quarterly_count, 90, "Meta trimestral 90"), width="stretch"
    )
    g3.plotly_chart(
        gauge_chart(semiannual_count, 180, "Meta semestral 180"), width="stretch"
    )

    # Captador Pie
    by_captador = df[C.COL_INT_CAPTADOR].value_counts().reset_index()
    by_captador.columns = ["Captador", "Contratos"]
    pie_fig = px.pie(
        by_captador,
        names="Captador",
        values="Contratos",
        title="Contratos por captador",
        color_discrete_sequence=px.colors.sequential.Pinkyl,
    )
    st.plotly_chart(pie_fig, width="stretch")

    # Status Bar
    status_df = status_counts.reindex(
        [C.STATUS_ASSINADO, C.STATUS_AGUARDANDO, C.STATUS_CANCELADO], fill_value=0
    ).reset_index()
    status_df.columns = ["Status", "Quantidade"]
    bar_fig = px.bar(
        status_df[status_df["Status"].isin([C.STATUS_ASSINADO, C.STATUS_AGUARDANDO])],
        x="Status",
        y="Quantidade",
        title="Assinados vs Aguardando",
        color="Status",
        color_discrete_map={
            C.STATUS_ASSINADO: C.COLOR_PRIMARY,
            C.STATUS_AGUARDANDO: C.COLOR_SECONDARY,
        },
    )
    st.plotly_chart(bar_fig, width="stretch")


def render_map_tab(df: pd.DataFrame):
    signed = df[df[C.COL_INT_STATUS] == C.STATUS_ASSINADO].copy()
    signed[C.COL_INT_REGION] = signed[C.COL_INT_STATE].map(C.ESTADO_REGIAO).fillna("")

    k1, k2 = st.columns([1, 1])
    k1.metric(
        "Estados presentes",
        signed[C.COL_INT_STATE].replace("", pd.NA).dropna().nunique(),
    )
    k2.metric(
        "Cidades presentes",
        signed[C.COL_INT_CITY].replace("", pd.NA).dropna().nunique(),
    )

    # Optimized Geocoding
    unique_locations = signed[[C.COL_INT_CITY, C.COL_INT_STATE]].drop_duplicates()
    location_map = {}
    for _, row in unique_locations.iterrows():
        c, s = row[C.COL_INT_CITY], row[C.COL_INT_STATE]
        if c and s:
            lat, lon = geo_service.get_coords(c, s)
            if lat is not None and lon is not None:
                location_map[(c, s)] = (lat, lon)

    geo_rows = []
    for _, row in signed.iterrows():
        k = (row.get(C.COL_INT_CITY, ""), row.get(C.COL_INT_STATE, ""))
        if k in location_map:
            lat, lon = location_map[k]
            geo_rows.append({"lat": lat, "lon": lon})

    if geo_rows:
        deck = pdk.Deck(
            layers=[
                pdk.Layer(
                    "ScatterplotLayer",
                    data=pd.DataFrame(geo_rows),
                    get_position="[lon, lat]",
                    get_radius=4000,
                    get_fill_color=[255, 45, 149],
                    pickable=True,
                )
            ],
            initial_view_state=pdk.ViewState(
                latitude=C.MAP_LAT_DEFAULT,
                longitude=C.MAP_LON_DEFAULT,
                zoom=C.MAP_ZOOM_DEFAULT,
            ),
            map_style="mapbox://styles/mapbox/dark-v9",
        )
        st.pydeck_chart(deck)

    # Charts with explicit column naming to avoid Plotly errors
    # State
    counts_state = signed[C.COL_INT_STATE].value_counts().reset_index()
    counts_state.columns = ["Estado", "Parceiros"]
    st.plotly_chart(
        px.bar(counts_state, x="Estado", y="Parceiros", title="Parceiros por estado"),
        width="stretch",
    )

    # City
    counts_city = signed[C.COL_INT_CITY].value_counts().reset_index()
    counts_city.columns = ["Cidade", "Parceiros"]
    st.plotly_chart(
        px.bar(counts_city, x="Cidade", y="Parceiros", title="Parceiros por cidade"),
        width="stretch",
    )

    # Region
    counts_region = signed[C.COL_INT_REGION].value_counts().reset_index()
    counts_region.columns = ["Região", "Parceiros"]
    st.plotly_chart(
        px.bar(counts_region, x="Região", y="Parceiros", title="Parceiros por região"),
        width="stretch",
    )


def render_financial_tab(df: pd.DataFrame):
    total = df[C.COL_INT_VALOR].sum()
    parceiros = (df[C.COL_INT_VALOR] * df[C.COL_INT_COMISSAO]).sum()
    equipe = 0.13 * (total - parceiros)
    liquido = total - parceiros - equipe

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Faturamento total", f"R$ {total:,.2f}")
    c2.metric("Comissão parceiros", f"R$ {parceiros:,.2f}")
    c3.metric("Comissão equipe (13%)", f"R$ {equipe:,.2f}")
    c4.metric("Líquido empresa", f"R$ {liquido:,.2f}")

    daily = df.groupby(df[C.COL_INT_DATA].dt.date)[C.COL_INT_VALOR].sum().reset_index()
    daily.columns = [C.COL_INT_DATA, C.COL_INT_VALOR]
    st.plotly_chart(
        px.line(daily, x=C.COL_INT_DATA, y=C.COL_INT_VALOR, title="Faturamento diário"),
        width="stretch",
    )


# -----------------------------------------------------------------------------
# Main App Logic
# -----------------------------------------------------------------------------

st.sidebar.title("Educa Mais Dashboard")
dados = get_dados(DEFAULT_SHEET_ID)
faturamento = get_faturamento(DEFAULT_SHEET_ID)

if not validate_columns(dados, [C.COL_INT_DT, C.COL_INT_STATUS]):
    st.stop()

# Date Filtering Logic
min_date = min(dados[C.COL_INT_DT].min(), faturamento[C.COL_INT_DATA].min()).date()
max_date = max(dados[C.COL_INT_DT].max(), faturamento[C.COL_INT_DATA].max()).date()

date_range = st.sidebar.date_input("Intervalo de datas", value=(min_date, max_date))
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = date_range[0], date_range[0]  # Fallback

months = sorted(dados[C.COL_INT_DT].dt.month.dropna().unique())
month_label = st.sidebar.selectbox(
    "Filtrar por mês", ["Todos"] + [f"{m:02d}" for m in months]
)
selected_month = int(month_label) if month_label != "Todos" else None

# Apply Filters
# Using standard masking since index optimization requires more complex setup for two distinct frames
mask_dados = (dados[C.COL_INT_DT].dt.date >= start_date) & (
    dados[C.COL_INT_DT].dt.date <= end_date
)
if selected_month:
    mask_dados &= dados[C.COL_INT_DT].dt.month == selected_month
dados_filtered = dados[mask_dados].copy()

mask_fat = (faturamento[C.COL_INT_DATA].dt.date >= start_date) & (
    faturamento[C.COL_INT_DATA].dt.date <= end_date
)
if selected_month:
    mask_fat &= faturamento[C.COL_INT_DATA].dt.month == selected_month
fat_filtered = faturamento[mask_fat].copy()

# Render Tabs
t1, t2, t3 = st.tabs(["Contratos", "Mapa", "Faturamento"])

with t1:
    render_contracts_tab(dados_filtered, end_date, selected_month)
with t2:
    render_map_tab(dados_filtered)
with t3:
    render_financial_tab(fat_filtered)
