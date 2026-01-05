import streamlit as st
import pandas as pd
import os
import logging
from datetime import date
from dotenv import load_dotenv

import constants as C
from services import data as data_service
from ui import contracts_tab, map_tab, financial_tab, forecast_tab, opportunity_tab, partners_tab, unit_analysis_tab

# Setup Logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

st.set_page_config(page_title=C.APP_TITLE, layout="wide")
load_dotenv()
DEFAULT_SHEET_ID = os.getenv("DEFAULT_SHEET_ID")

# -----------------------------------------------------------------------------
# Main App Logic
# -----------------------------------------------------------------------------

# Add Logo to Sidebar
st.sidebar.image("Ativo 10.png", use_container_width=True)

st.sidebar.title(C.APP_TITLE)
if st.sidebar.button(C.UI_LABEL_RELOAD_DATA):
    st.cache_data.clear()
    st.rerun()

dados = data_service.get_dados(DEFAULT_SHEET_ID)
faturamento = data_service.get_faturamento(DEFAULT_SHEET_ID)

if not data_service.validate_columns(dados, [C.COL_INT_DT, C.COL_INT_STATUS]):
    st.stop()

# Date Filtering Logic
# Handle cases where dataframes might be empty or have null dates
min_dt_dados = dados[C.COL_INT_DT].min()
min_dt_fat = faturamento[C.COL_INT_DATA].min()
max_dt_dados = dados[C.COL_INT_DT].max()
max_dt_fat = faturamento[C.COL_INT_DATA].max()

# Default to today if no data
default_date = date.today()
min_date = default_date
max_date = default_date

if pd.notna(min_dt_dados) and pd.notna(min_dt_fat):
    min_date = min(min_dt_dados, min_dt_fat).date()
elif pd.notna(min_dt_dados):
    min_date = min_dt_dados.date()
elif pd.notna(min_dt_fat):
    min_date = min_dt_fat.date()

if pd.notna(max_dt_dados) and pd.notna(max_dt_fat):
    max_date = max(max_dt_dados, max_dt_fat).date()
elif pd.notna(max_dt_dados):
    max_date = max_dt_dados.date()
elif pd.notna(max_dt_fat):
    max_date = max_dt_fat.date()

date_range = st.sidebar.date_input(C.UI_LABEL_DATE_RANGE, value=(min_date, max_date))
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    # Handle single date selection or invalid range
    if isinstance(date_range, tuple) and len(date_range) == 1:
         start_date, end_date = date_range[0], date_range[0]
    elif not isinstance(date_range, tuple):
         start_date, end_date = date_range, date_range
    else:
         start_date, end_date = min_date, max_date

# Year and Month Filters
all_dates = pd.concat([dados[C.COL_INT_DT], faturamento[C.COL_INT_DATA]]).dropna()
years = sorted(all_dates.dt.year.unique(), reverse=True)
year_label = st.sidebar.selectbox(
    "Filtrar por Ano", [C.UI_LABEL_ALL] + [str(int(y)) for y in years]
)
selected_year = int(year_label) if year_label != C.UI_LABEL_ALL else None

if selected_year:
    # Filter dates for the selected year from both datasets
    dates_in_year = all_dates[all_dates.dt.year == selected_year]
    months_in_year = sorted(dates_in_year.dt.month.unique())
else:
    months_in_year = sorted(all_dates.dt.month.unique())

month_options = [C.UI_LABEL_ALL] + [
    C.MONTH_NAMES.get(int(m), f"{int(m):02d}") for m in months_in_year
]
month_label = st.sidebar.selectbox(C.UI_LABEL_FILTER_MONTH, month_options)

selected_month = None
if month_label != C.UI_LABEL_ALL:
    # Reverse lookup month number
    for m_num, m_name in C.MONTH_NAMES.items():
        if m_name == month_label:
            selected_month = m_num
            break

# Contract Type Filter
contract_type_options = [C.UI_LABEL_ALL, C.CONTRACT_TYPE_UI_TECNICO, C.CONTRACT_TYPE_UI_POS]
selected_contract_type = st.sidebar.radio(C.UI_LABEL_CONTRACT_TYPE, contract_type_options)

# Geographic Filters
unique_regions = sorted([r for r in dados[C.COL_INT_REGION].unique() if r])
selected_regions = st.sidebar.multiselect(C.UI_LABEL_FILTER_REGION, unique_regions)

# State Filter (dependent on Region)
if selected_regions:
    available_states = sorted(
        [
            s
            for s in dados[C.COL_INT_STATE].unique()
            if s and C.ESTADO_REGIAO.get(s) in selected_regions
        ]
    )
else:
    available_states = sorted([s for s in dados[C.COL_INT_STATE].unique() if s])

selected_states = st.sidebar.multiselect(C.UI_LABEL_FILTER_STATE, available_states)

# City Filter (dependent on State) - Cascading Filter
if selected_states:
    available_cities = sorted(
        [
            c
            for c in dados[dados[C.COL_INT_STATE].isin(selected_states)][C.COL_INT_CITY].unique()
            if c
        ]
    )
else:
    # If no state selected, show all cities (or maybe none to avoid clutter, but let's show all for now)
    available_cities = sorted([c for c in dados[C.COL_INT_CITY].unique() if c])

selected_cities = st.sidebar.multiselect("Filtrar por Cidade", available_cities)

# Apply Filters
# Using standard masking since index optimization requires more complex setup for two distinct frames
mask_dados = (dados[C.COL_INT_DT].dt.date >= start_date) & (
    dados[C.COL_INT_DT].dt.date <= end_date
)
if selected_year:
    mask_dados &= dados[C.COL_INT_DT].dt.year == selected_year

if selected_month:
    mask_dados &= dados[C.COL_INT_DT].dt.month == selected_month

if selected_contract_type == C.CONTRACT_TYPE_UI_TECNICO:
    mask_dados &= dados[C.COL_INT_CONTRACT_TYPE].isin(
        [C.CONTRACT_TYPE_NORMAL, C.CONTRACT_TYPE_50]
    )
elif selected_contract_type == C.CONTRACT_TYPE_UI_POS:
    mask_dados &= dados[C.COL_INT_CONTRACT_TYPE] == C.CONTRACT_TYPE_POS

if selected_regions:
    mask_dados &= dados[C.COL_INT_REGION].isin(selected_regions)

if selected_states:
    mask_dados &= dados[C.COL_INT_STATE].isin(selected_states)

if selected_cities:
    mask_dados &= dados[C.COL_INT_CITY].isin(selected_cities)

dados_filtered = dados[mask_dados].copy()

mask_fat = (faturamento[C.COL_INT_DATA].dt.date >= start_date) & (
    faturamento[C.COL_INT_DATA].dt.date <= end_date
)
if selected_year:
    mask_fat &= faturamento[C.COL_INT_DATA].dt.year == selected_year

if selected_month:
    mask_fat &= faturamento[C.COL_INT_DATA].dt.month == selected_month

if selected_contract_type == C.CONTRACT_TYPE_UI_TECNICO:
    mask_fat &= faturamento[C.COL_INT_FINANCIAL_TYPE] == C.FINANCIAL_TYPE_TECNICO
elif selected_contract_type == C.CONTRACT_TYPE_UI_POS:
    mask_fat &= faturamento[C.COL_INT_FINANCIAL_TYPE] == C.FINANCIAL_TYPE_POS

fat_filtered = faturamento[mask_fat].copy()

# Render Tabs
t1, t2, t3, t4, t5, t6, t7 = st.tabs(
    [C.TAB_NAME_CONTRACTS, C.TAB_NAME_MAP, C.TAB_NAME_FINANCIAL, C.TAB_NAME_FORECAST, C.TAB_NAME_OPPORTUNITY, C.TAB_NAME_PARTNERS, C.TAB_NAME_UNIT_ANALYSIS]
)

with t1:
    contracts_tab.render(dados_filtered, end_date, selected_month)
with t2:
    map_tab.render(dados_filtered)
with t3:
    financial_tab.render(fat_filtered, faturamento, end_date, selected_month)
with t4:
    forecast_tab.render(dados_filtered, fat_filtered)
with t5:
    opportunity_tab.render(dados_filtered)
with t6:
    partners_tab.render(fat_filtered)
with t7:
    unit_analysis_tab.render(dados_filtered)
