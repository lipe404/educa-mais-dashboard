import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, date, timedelta
from dateutil import parser
from io import StringIO
import os
import logging
from dotenv import load_dotenv

from geocoding_service import GeocodingService
import forecasting
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
    col_a, col_b, col_c, col_d = st.columns([1, 1, 1, 1])

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

    month_mask = (signed_df[C.COL_INT_DT].dt.year == focus_year) & (
        signed_df[C.COL_INT_DT].dt.month == focus_month
    )
    month_count = signed_df[month_mask].shape[0]

    week_end_date = end_date if isinstance(end_date, date) else date.today()
    week_start_date = week_end_date - timedelta(days=week_end_date.weekday())
    week_mask = (signed_df[C.COL_INT_DT].dt.date >= week_start_date) & (
        signed_df[C.COL_INT_DT].dt.date <= (week_start_date + timedelta(days=6))
    )
    week_count = signed_df[week_mask].shape[0]

    col_c.metric("Assinados este mês", month_count)
    col_d.metric("Assinados esta semana", week_count)

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

    signed_only = df[df[C.COL_INT_STATUS] == C.STATUS_ASSINADO].copy()
    signed_only = signed_only.dropna(subset=[C.COL_INT_DT])
    signed_only["_ano"] = signed_only[C.COL_INT_DT].dt.year
    signed_only["_mes"] = signed_only[C.COL_INT_DT].dt.month
    monthly = (
        signed_only.groupby(["_ano", "_mes"]).size().reset_index(name="Contratos")
    )
    pt_months = {
        1: "Janeiro",
        2: "Fevereiro",
        3: "Março",
        4: "Abril",
        5: "Maio",
        6: "Junho",
        7: "Julho",
        8: "Agosto",
        9: "Setembro",
        10: "Outubro",
        11: "Novembro",
        12: "Dezembro",
    }
    monthly["Mês"] = monthly.apply(
        lambda r: f"{pt_months.get(int(r['_mes']), str(int(r['_mes'])))} {int(r['_ano'])}",
        axis=1,
    )
    monthly = monthly.sort_values(["_ano", "_mes"]) 
    fig_month = px.bar(
        monthly,
        x="Mês",
        y="Contratos",
        title="Contratos assinados por mês",
        color_discrete_sequence=[C.COLOR_PRIMARY],
    )
    st.plotly_chart(fig_month, width="stretch")


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
            geo_rows.append(
                {
                    "lat": lat,
                    "lon": lon,
                    "cidade": row.get(C.COL_INT_CITY, ""),
                    "estado": row.get(C.COL_INT_STATE, ""),
                }
            )

    if geo_rows:
        geo_df = pd.DataFrame(geo_rows)
        # Using Plotly Scatter Mapbox for better visibility and reliability (no token needed for open-street-map)
        fig_map = px.scatter_mapbox(
            geo_df,
            lat="lat",
            lon="lon",
            hover_name="cidade",
            hover_data={"estado": True, "lat": False, "lon": False},
            color_discrete_sequence=[C.COLOR_SECONDARY],
            zoom=3,
            center={"lat": C.MAP_LAT_DEFAULT, "lon": C.MAP_LON_DEFAULT},
            title="Distribuição Geográfica de Contratos Assinados",
        )
        fig_map.update_layout(
            mapbox_style="open-street-map",
            height=600,
            margin={"r": 0, "t": 30, "l": 0, "b": 0},
        )
        st.plotly_chart(fig_map, width="stretch")

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


def render_financial_tab(df: pd.DataFrame, full_df: pd.DataFrame, end_date: date, selected_month: int | None):
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

    m = df.dropna(subset=[C.COL_INT_DATA]).copy()
    m["_ano"] = m[C.COL_INT_DATA].dt.year
    m["_mes"] = m[C.COL_INT_DATA].dt.month
    monthly = m.groupby(["_ano", "_mes"])[C.COL_INT_VALOR].sum().reset_index()
    pt_months = {
        1: "Janeiro",
        2: "Fevereiro",
        3: "Março",
        4: "Abril",
        5: "Maio",
        6: "Junho",
        7: "Julho",
        8: "Agosto",
        9: "Setembro",
        10: "Outubro",
        11: "Novembro",
        12: "Dezembro",
    }
    monthly["Mês"] = monthly.apply(
        lambda r: f"{pt_months.get(int(r['_mes']), str(int(r['_mes'])))} {int(r['_ano'])}",
        axis=1,
    )
    monthly = monthly.sort_values(["_ano", "_mes"]) 
    st.plotly_chart(
        px.bar(
            monthly,
            x="Mês",
            y=C.COL_INT_VALOR,
            title="Faturamento por mês",
            color_discrete_sequence=[C.COLOR_PRIMARY],
        ),
        width="stretch",
    )

    now = date.today()
    focus_year = end_date.year if isinstance(end_date, date) else now.year
    focus_month = selected_month if selected_month is not None else now.month
    prev_year = focus_year if focus_month > 1 else focus_year - 1
    prev_month = focus_month - 1 if focus_month > 1 else 12
    cur_mask = (full_df[C.COL_INT_DATA].dt.year == focus_year) & (full_df[C.COL_INT_DATA].dt.month == focus_month)
    prev_mask = (full_df[C.COL_INT_DATA].dt.year == prev_year) & (full_df[C.COL_INT_DATA].dt.month == prev_month)
    cur_total_month = float(full_df.loc[cur_mask, C.COL_INT_VALOR].sum())
    prev_total_month = float(full_df.loc[prev_mask, C.COL_INT_VALOR].sum())
    diff = cur_total_month - prev_total_month
    progress_pct = (cur_total_month / prev_total_month * 100.0) if prev_total_month > 0 else None
    k1, k2, k3 = st.columns(3)
    k1.metric("Faturamento mês atual", f"R$ {cur_total_month:,.2f}")
    k2.metric("Meta mês passado", f"R$ {prev_total_month:,.2f}")
    k3.metric("Acima do mês passado" if diff > 0 else "Falta para igualar mês passado", f"R$ {abs(diff):,.2f}", delta=(f"{progress_pct:.1f}%" if progress_pct is not None else None))

    st.markdown("### Simulador de faturamento adicional")
    sim_add = st.number_input("Valor adicional (R$)", min_value=0.0, step=100.0, value=0.0)
    avg_comissao = (parceiros / total) if total > 0 else 0.0
    sim_total = total + sim_add
    sim_parceiros = parceiros + sim_add * avg_comissao
    sim_equipe = 0.13 * (sim_total - sim_parceiros)
    sim_liquido = sim_total - sim_parceiros - sim_equipe
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Faturamento total (simulado)", f"R$ {sim_total:,.2f}")
    s2.metric("Comissão parceiros (simulado)", f"R$ {sim_parceiros:,.2f}")
    s3.metric("Comissão equipe (13%) (simulado)", f"R$ {sim_equipe:,.2f}")
    s4.metric("Líquido empresa (simulado)", f"R$ {sim_liquido:,.2f}")
    cur_total_month_sim = cur_total_month + sim_add
    diff_sim = cur_total_month_sim - prev_total_month
    progress_pct_sim = (cur_total_month_sim / prev_total_month * 100.0) if prev_total_month > 0 else None
    st.metric("Acima do mês passado (simulado)" if diff_sim > 0 else "Falta p/ igualar mês passado (simulado)", f"R$ {abs(diff_sim):,.2f}", delta=(f"{progress_pct_sim:.1f}%" if progress_pct_sim is not None else None))


def render_forecast_tab(df: pd.DataFrame):
    import forecasting  # Late import or move to top? Python allows it. I'll move to top later or implicitly here.

    st.markdown("### Previsão de Contratos")

    c1, c2 = st.columns(2)
    with c1:
        algo = st.selectbox(
            "Algoritmo",
            [
                "Prophet (Facebook AI)",
                "Holt-Winters (Sazonal)",
            ],
        )
    with c2:
        horizon_label = st.selectbox(
            "Horizonte",
            [
                "1 Semana",
                "2 Semanas",
                "3 Semanas",
                "1 Mês",
                "3 Meses",
                "6 Meses",
                "1 Ano",
            ],
        )

    horizon_map = {
        "1 Semana": 7,
        "2 Semanas": 14,
        "3 Semanas": 21,
        "1 Mês": 30,
        "3 Meses": 90,
        "6 Meses": 180,
        "1 Ano": 365,
    }
    days = horizon_map[horizon_label]

    # Filter for ONLY Signed Contracts
    # Essential to avoid inflating numbers with "Aguardando"/"Cancelado"
    signed_df = df[df[C.COL_INT_STATUS] == C.STATUS_ASSINADO].copy()

    # Prepare data for forecast (Count 1 per row)
    df_input = signed_df.copy()
    df_input["Contratos"] = 1

    # Generate
    try:
        final_df = forecasting.generate_forecast(
            df_input, C.COL_INT_DT, "Contratos", algo, days
        )

        # Calculate Total Predicted
        future_mask = final_df["Type"] == "Previsão"
        total_predicted = int(final_df[future_mask]["Contratos"].sum())

        # Calculate Total (Historical + Predicted)
        # We count rows in the original filtered df for "Contratos Assinados"
        total_historical = len(signed_df)
        total_final = total_historical + total_predicted

        # Display Metrics in Columns
        m1, m2 = st.columns(2)
        m1.metric(label=f"Novos Contratos ({horizon_label})", value=total_predicted)
        m2.metric(
            label="Total Final Esperado",
            value=total_final,
            delta=f"+{total_predicted} novos",
        )

        # Plot
        fig = px.line(
            final_df,
            x=C.COL_INT_DT,
            y="Contratos",
            color="Type",
            title=f"Previsão de Novos Contratos Diários - {algo}",
            color_discrete_map={
                "Histórico": C.COLOR_PRIMARY,
                "Previsão": C.COLOR_FORECAST,
            },
        )
        st.plotly_chart(fig, width="stretch")

        # AI Insights
        st.markdown("---")
        insights = forecasting.generate_smart_insights(
            df_input, C.COL_INT_DT, "Contratos", final_df
        )
        st.info(insights)

    except Exception as e:
        logger.error(f"Forecast error: {e}")
        st.error(f"Erro ao gerar previsão: {e}")
        if "não instalada" in str(e):
            st.warning(
                "Dica: Verifique se as bibliotecas 'prophet' e 'statsmodels' estão instaladas."
            )


st.sidebar.title("Educa Mais Dashboard")
if st.sidebar.button("Recarregar dados"):
    st.cache_data.clear()
    st.rerun()
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
    "Filtrar por mês", ["Todos"] + [f"{int(m):02d}" for m in months]
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
t1, t2, t3, t4 = st.tabs(["Contratos", "Mapa", "Faturamento", "Previsões"])

with t1:
    render_contracts_tab(dados_filtered, end_date, selected_month)
with t2:
    render_map_tab(dados_filtered)
with t3:
    render_financial_tab(fat_filtered, faturamento, end_date, selected_month)
with t4:
    render_forecast_tab(dados_filtered)
