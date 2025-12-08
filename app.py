import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, date
from dateutil import parser
from functools import lru_cache
from geopy.geocoders import Nominatim
from io import StringIO
import os
from dotenv import load_dotenv
import pydeck as pdk
from geocoding_service import GeocodingService

st.set_page_config(page_title="Educa Mais Dashboard", layout="wide")
load_dotenv()
DEFAULT_SHEET_ID = os.getenv("DEFAULT_SHEET_ID")


@st.cache_data(show_spinner=False, ttl=3600)
def load_sheet(sheet_id: str, sheet_name: str) -> pd.DataFrame:
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        df = pd.read_csv(StringIO(r.text))
        return df
    except Exception as e:
        st.error(f"Erro ao carregar aba '{sheet_name}': {e}")
        return pd.DataFrame()


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


@st.cache_data(show_spinner=False, ttl=3600)
def get_dados(sheet_id: str) -> pd.DataFrame:
    df = load_sheet(sheet_id, "Dados")
    if "TIMESTAMP" in df.columns:
        df["_dt"] = df["TIMESTAMP"].apply(parse_datetime_any)
    else:
        df["_dt"] = None
    if "CONTRATO ASSINADO" in df.columns:
        df["_status"] = df["CONTRATO ASSINADO"].astype(str).str.strip().str.upper()
    else:
        df["_status"] = ""
    if "CAPTADOR" in df.columns:
        df["_captador"] = df["CAPTADOR"].astype(str).str.strip()
    else:
        df["_captador"] = ""
    if "ESTADO" in df.columns:
        df["_estado"] = df["ESTADO"].astype(str).str.strip().str.upper()
    else:
        df["_estado"] = ""
    if "CIDADE" in df.columns:
        df["_cidade"] = df["CIDADE"].astype(str).str.strip()
    else:
        df["_cidade"] = ""
    if "CEP" in df.columns:
        df["_cep"] = df["CEP"].astype(str).str.strip()
    else:
        df["_cep"] = ""
    return df


@st.cache_data(show_spinner=False, ttl=3600)
def get_faturamento(sheet_id: str) -> pd.DataFrame:
    df = load_sheet(sheet_id, "FATURAMENTO")
    if "VALOR" in df.columns:
        df["_valor"] = df["VALOR"].apply(to_float_any)
    else:
        df["_valor"] = 0.0
    if "COMISSÃO" in df.columns:
        df["_comissao"] = df["COMISSÃO"].apply(lambda x: to_float_any(x) / 100.0)
    else:
        df["_comissao"] = 0.0
    if "DATA" in df.columns:
        df["_data"] = df["DATA"].apply(parse_datetime_any)
    else:
        df["_data"] = None
    return df


ESTADO_REGIAO = {
    "AC": "Norte",
    "AL": "Nordeste",
    "AP": "Norte",
    "AM": "Norte",
    "BA": "Nordeste",
    "CE": "Nordeste",
    "DF": "Centro-Oeste",
    "ES": "Sudeste",
    "GO": "Centro-Oeste",
    "MA": "Nordeste",
    "MT": "Centro-Oeste",
    "MS": "Centro-Oeste",
    "MG": "Sudeste",
    "PA": "Norte",
    "PB": "Nordeste",
    "PR": "Sul",
    "PE": "Nordeste",
    "PI": "Nordeste",
    "RJ": "Sudeste",
    "RN": "Nordeste",
    "RS": "Sul",
    "RO": "Norte",
    "RR": "Norte",
    "SC": "Sul",
    "SP": "Sudeste",
    "SE": "Nordeste",
    "TO": "Norte",
}

# Geocoding agora é tratado via serviço dedicado
geo_service = GeocodingService()


def gauge_chart(value: float, target: float, title: str) -> go.Figure:
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value,
            title={"text": title},
            gauge={
                "axis": {"range": [0, target]},
                "bar": {"color": "#ff2d95"},
                "bgcolor": "#0b1437",
            },
        )
    )
    fig.update_layout(height=250, margin=dict(l=10, r=10, t=40, b=10))
    return fig


st.sidebar.title("Educa Mais Dashboard")
dados = get_dados(DEFAULT_SHEET_ID)
faturamento = get_faturamento(DEFAULT_SHEET_ID)

min_dt_candidates = []
if "_dt" in dados.columns:
    min_dt_candidates.append(dados["_dt"].dropna().min())
if "_data" in faturamento.columns:
    min_dt_candidates.append(faturamento["_data"].dropna().min())
max_dt_candidates = []
if "_dt" in dados.columns:
    max_dt_candidates.append(dados["_dt"].dropna().max())
if "_data" in faturamento.columns:
    max_dt_candidates.append(faturamento["_data"].dropna().max())
default_start = (
    min_dt_candidates[0] if len(min_dt_candidates) else pd.Timestamp(date.today())
).date()
default_end = (
    max_dt_candidates[0] if len(max_dt_candidates) else pd.Timestamp(date.today())
).date()
date_range = st.sidebar.date_input(
    "Intervalo de datas", value=(default_start, default_end)
)
if isinstance(date_range, tuple):
    start_date, end_date = date_range
else:
    start_date, end_date = date_range, date_range
months_available = sorted(dados.dropna(subset=["_dt"])["_dt"].dt.month.unique())
month_label_options = ["Todos"] + [f"{m:02d}" for m in months_available]
month_label = st.sidebar.selectbox(
    "Filtrar por mês", options=month_label_options, index=0
)
selected_month = None if month_label == "Todos" else int(month_label)

dados_base = dados.dropna(subset=["_dt"]).copy()
dados_base = dados_base[
    (dados_base["_dt"].dt.date >= start_date) & (dados_base["_dt"].dt.date <= end_date)
]
if selected_month is not None:
    dados_base = dados_base[dados_base["_dt"].dt.month == selected_month]

faturamento_base = faturamento.dropna(subset=["_data"]).copy()
faturamento_base = faturamento_base[
    (faturamento_base["_data"].dt.date >= start_date)
    & (faturamento_base["_data"].dt.date <= end_date)
]
if selected_month is not None:
    faturamento_base = faturamento_base[
        faturamento_base["_data"].dt.month == selected_month
    ]

tabs = st.tabs(["Contratos", "Mapa", "Faturamento"])

with tabs[0]:
    col_a, col_b, col_c, col_d = st.columns([1, 1, 1, 1])

    # -------------------------------------------------------------------------
    # OPTIMIZATION: Calc status counts once
    # -------------------------------------------------------------------------
    status_counts_series = dados_base["_status"].value_counts()
    signed_count = int(status_counts_series.get("ASSINADO", 0))
    waiting_count = int(status_counts_series.get("AGUARDANDO", 0))

    col_a.metric("Contratos assinados", signed_count)
    col_b.metric("Contratos aguardando", waiting_count)
    now = date.today()
    focus_year = end_date.year if isinstance(end_date, date) else now.year
    focus_month = selected_month if selected_month is not None else now.month
    dados_signed = dados_base[dados_base["_status"] == "ASSINADO"].copy()
    month_count = int(
        dados_signed[
            (
                dados_signed["_dt"].dt.year
                == (focus_year if selected_month is not None else now.year)
            )
            & (dados_signed["_dt"].dt.month == focus_month)
        ].shape[0]
    )
    q_start = ((focus_month - 1) // 3) * 3 + 1
    quarterly_mask = (
        (dados_signed["_dt"].dt.year == focus_year)
        & (dados_signed["_dt"].dt.month >= q_start)
        & (dados_signed["_dt"].dt.month <= q_start + 2)
    )
    quarterly_count = int(dados_signed[quarterly_mask].shape[0])
    sem_start = 1 if focus_month <= 6 else 7
    semestral_mask = (
        (dados_signed["_dt"].dt.year == focus_year)
        & (dados_signed["_dt"].dt.month >= sem_start)
        & (dados_signed["_dt"].dt.month <= sem_start + 5)
    )
    semiannual_count = int(dados_signed[semestral_mask].shape[0])
    g1, g2, g3 = st.columns([1, 1, 1])
    g1.plotly_chart(gauge_chart(month_count, 30, "Meta mensal 30"), width="stretch")
    g2.plotly_chart(
        gauge_chart(quarterly_count, 90, "Meta trimestral 90"), width="stretch"
    )
    g3.plotly_chart(
        gauge_chart(semiannual_count, 180, "Meta semestral 180"), width="stretch"
    )
    by_captador = dados_base["_captador"].value_counts().reset_index()
    by_captador.columns = ["Captador", "Contratos"]
    pie_fig = px.pie(
        by_captador,
        names="Captador",
        values="Contratos",
        title="Contratos por captador",
        color_discrete_sequence=px.colors.sequential.Pinkyl,
    )
    st.plotly_chart(pie_fig, width="stretch")
    status_counts = status_counts_series.reindex(
        ["ASSINADO", "AGUARDANDO", "CANCELADO"], fill_value=0
    ).reset_index()
    status_counts.columns = ["Status", "Quantidade"]
    bar_fig = px.bar(
        status_counts[status_counts["Status"].isin(["ASSINADO", "AGUARDANDO"])],
        x="Status",
        y="Quantidade",
        title="Assinados vs Aguardando",
        color="Status",
        color_discrete_map={"ASSINADO": "#2d9fff", "AGUARDANDO": "#ff2d95"},
    )
    st.plotly_chart(bar_fig, width="stretch")

with tabs[1]:
    signed = dados_base[dados_base["_status"] == "ASSINADO"].copy()
    signed["_regiao"] = signed["_estado"].map(ESTADO_REGIAO).fillna("")
    states_present = signed["_estado"].replace("", pd.NA).dropna().nunique()
    cities_present = signed["_cidade"].replace("", pd.NA).dropna().nunique()
    k1, k2 = st.columns([1, 1])
    k1.metric("Estados presentes", int(states_present))
    k2.metric("Cidades presentes", int(cities_present))
    geo_rows = []

    # -------------------------------------------------------------------------
    # OPTIMIZATION: Geocode ONLY unique (city, state) pairs first
    # -------------------------------------------------------------------------
    # Extract unique pairs
    unique_locations = signed[["_cidade", "_estado"]].drop_duplicates()

    # Pre-fetch/cache results
    location_map = {}
    for _, row in unique_locations.iterrows():
        c, s = row["_cidade"], row["_estado"]
        if c and s:
            # This will hit local SQLite cache or API
            lat, lon = geo_service.get_coords(c, s)
            if lat is not None and lon is not None:
                location_map[(c, s)] = (lat, lon)

    # Build list using lookup
    # Iterate original SIGNED frame to render one point per contract?
    # Actually, usually map shows density or markers.
    # If we want 1 marker per contract, we iterate signed.
    # If we want 1 marker per city, we use unique_locations.
    # The original loop iterated 'signed', implying 1 dot per contract
    # (multiple dots on top of each other if same city).
    # We will keep behavior: 1 row in geo_df = 1 contract.

    for _, row in signed.iterrows():
        city = row.get("_cidade", "")
        state = row.get("_estado", "")
        if (city, state) in location_map:
            lat, lon = location_map[(city, state)]
            geo_rows.append({"lat": lat, "lon": lon, "cidade": city, "estado": state})
    if len(geo_rows) > 0:
        geo_df = pd.DataFrame(geo_rows)
        layer = pdk.Layer(
            "ScatterplotLayer",
            data=geo_df,
            get_position="[lon, lat]",
            get_radius=4000,
            get_fill_color=[255, 45, 149],
            pickable=True,
        )
        view_state = pdk.ViewState(latitude=-14.235, longitude=-51.9253, zoom=3.5)
        deck = pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            map_style="mapbox://styles/mapbox/dark-v9",
        )
        st.pydeck_chart(deck)
    by_state = signed["_estado"].value_counts().reset_index()
    by_state.columns = ["Estado", "Parceiros"]
    st.plotly_chart(
        px.bar(by_state, x="Estado", y="Parceiros", title="Parceiros por estado"),
        width="stretch",
    )
    by_city = signed["_cidade"].value_counts().reset_index()
    by_city.columns = ["Cidade", "Parceiros"]
    st.plotly_chart(
        px.bar(by_city, x="Cidade", y="Parceiros", title="Parceiros por cidade"),
        width="stretch",
    )
    by_region = signed["_regiao"].value_counts().reset_index()
    by_region.columns = ["Região", "Parceiros"]
    st.plotly_chart(
        px.bar(by_region, x="Região", y="Parceiros", title="Parceiros por região"),
        width="stretch",
    )

with tabs[2]:
    total = faturamento_base["_valor"].sum()
    parceiros = (faturamento_base["_valor"] * faturamento_base["_comissao"]).sum()
    equipe = 0.13 * (total - parceiros)
    liquido = total - parceiros - equipe
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Faturamento total", f"R$ {total:,.2f}")
    c2.metric("Comissão parceiros", f"R$ {parceiros:,.2f}")
    c3.metric("Comissão equipe (13%)", f"R$ {equipe:,.2f}")
    c4.metric("Líquido empresa", f"R$ {liquido:,.2f}")
    faturamento_valid = faturamento_base.copy()
    faturamento_valid["ano"] = faturamento_valid["_data"].dt.year
    faturamento_valid["mes"] = faturamento_valid["_data"].dt.month
    daily = (
        faturamento_valid.groupby(faturamento_valid["_data"].dt.date)["_valor"]
        .sum()
        .reset_index()
    )
    monthly = faturamento_valid.groupby(["ano", "mes"])["_valor"].sum().reset_index()
    daily_fig = px.line(daily, x="_data", y="_valor", title="Faturamento diário")
    st.plotly_chart(daily_fig, width="stretch")
    monthly["label"] = (
        monthly["mes"].astype(str).str.zfill(2) + "/" + monthly["ano"].astype(str)
    )
    monthly_fig = px.line(monthly, x="label", y="_valor", title="Faturamento mensal")
    st.plotly_chart(monthly_fig, width="stretch")
