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

st.set_page_config(page_title=C.APP_TITLE, page_icon="icon-blue-to-pink.ico", layout="wide")
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
# Custom CSS for Tab Icons
st.markdown(
    """
    <style>
        /* Tab Icons */
        div[data-testid="stTabs"] button > div[data-testid="stMarkdownContainer"] > p::before {
            content: "";
            display: inline-block;
            width: 20px;
            height: 20px;
            margin-right: 8px;
            background-size: contain;
            background-repeat: no-repeat;
            vertical-align: sub;
        }

        /* 1. Contratos - File Text */
        div[data-testid="stTabs"] button:nth-of-type(1) > div > p::before {
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%232d9fff' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z'%3E%3C/path%3E%3Cpolyline points='14 2 14 8 20 8'%3E%3C/polyline%3E%3Cline x1='16' y1='13' x2='8' y2='13'%3E%3C/line%3E%3Cline x1='16' y1='17' x2='8' y2='17'%3E%3C/line%3E%3Cpolyline points='10 9 9 9 8 9'%3E%3C/polyline%3E%3C/svg%3E");
        }

        /* 2. Mapa - Map Pin */
        div[data-testid="stTabs"] button:nth-of-type(2) > div > p::before {
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%232d9fff' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z'%3E%3C/path%3E%3Ccircle cx='12' cy='10' r='3'%3E%3C/circle%3E%3C/svg%3E");
        }

        /* 3. Faturamento - Dollar Sign */
        div[data-testid="stTabs"] button:nth-of-type(3) > div > p::before {
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%232d9fff' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cline x1='12' y1='1' x2='12' y2='23'%3E%3C/line%3E%3Cpath d='M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6'%3E%3C/path%3E%3C/svg%3E");
        }

        /* 4. Previsões - Trending Up */
        div[data-testid="stTabs"] button:nth-of-type(4) > div > p::before {
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%232d9fff' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='23 6 13.5 15.5 8.5 10.5 1 18'%3E%3C/polyline%3E%3Cpolyline points='17 6 23 6 23 12'%3E%3C/polyline%3E%3C/svg%3E");
        }

        /* 5. Oportunidade - Target */
        div[data-testid="stTabs"] button:nth-of-type(5) > div > p::before {
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%232d9fff' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='10'%3E%3C/circle%3E%3Ccircle cx='12' cy='12' r='6'%3E%3C/circle%3E%3Ccircle cx='12' cy='12' r='2'%3E%3C/circle%3E%3C/svg%3E");
        }

        /* 6. Parceiros - Users */
        div[data-testid="stTabs"] button:nth-of-type(6) > div > p::before {
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%232d9fff' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2'%3E%3C/path%3E%3Ccircle cx='9' cy='7' r='4'%3E%3C/circle%3E%3Cpath d='M23 21v-2a4 4 0 0 0-3-3.87'%3E%3C/path%3E%3Cpath d='M16 3.13a4 4 0 0 1 0 7.75'%3E%3C/path%3E%3C/svg%3E");
        }

        /* 7. Análise Unitária - Monitor/Dashboard */
        div[data-testid="stTabs"] button:nth-of-type(7) > div > p::before {
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%232d9fff' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='2' y='3' width='20' height='14' rx='2' ry='2'%3E%3C/rect%3E%3Cline x1='8' y1='21' x2='16' y2='21'%3E%3C/line%3E%3Cline x1='12' y1='17' x2='12' y2='21'%3E%3C/line%3E%3C/svg%3E");
        }
    </style>
    """,
    unsafe_allow_html=True
)

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
