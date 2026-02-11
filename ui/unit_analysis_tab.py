import streamlit as st
import pandas as pd
import plotly.express as px
import constants as C
from typing import Callable, List, Tuple, Dict, Any, Optional
from geocoding_service import GeocodingService


def _check_authentication(access_key: str) -> bool:
    """Handles access control for the Unit Analysis tab."""
    if "unit_analysis_access" not in st.session_state:
        st.session_state["unit_analysis_access"] = False

    if not st.session_state["unit_analysis_access"]:
        st.info(C.UI_LABEL_ENTER_KEY_MSG)
        key = st.text_input(
            C.UI_LABEL_ACCESS_KEY, type="password", key="unit_analysis_access_key"
        )
        if st.button("Acessar", key="btn_unit_access"):
            if not access_key:
                st.error("Erro de configuração: KEY_API não definida no ambiente.")
                return False

            if key == access_key:
                st.session_state["unit_analysis_access"] = True
                st.rerun()
            else:
                st.error("Chave de acesso inválida.")
        return False
    return True


def _get_base_location(partner_data: pd.DataFrame) -> Tuple[str, str]:
    """Determines the base location (City, State) for a partner."""
    if partner_data.empty:
        return "", ""
    try:
        city = partner_data[C.COL_INT_CITY].mode().iloc[0]
        state = partner_data[C.COL_INT_STATE].mode().iloc[0]
        return str(city), str(state)
    except (IndexError, KeyError, ValueError):
        # Fallback to first row
        try:
            city = partner_data[C.COL_INT_CITY].iloc[0]
            state = partner_data[C.COL_INT_STATE].iloc[0]
            return str(city), str(state)
        except (IndexError, KeyError):
            return "", ""


def _run_ai_analysis(
    city: str,
    state: str,
    dados_df: pd.DataFrame,
    build_oportunidade_por_uf: Callable[[pd.DataFrame, List[str]], pd.DataFrame],
    geo_service: GeocodingService,
) -> None:
    """Runs the AI analysis for the selected unit."""
    st.info(f"Análise de Inteligência de Mercado para {city}-{state} em desenvolvimento.")
    st.warning("Esta funcionalidade estará disponível em breve.")


def _render_partner_header(dados_df: pd.DataFrame) -> Tuple[Optional[str], Optional[pd.DataFrame], Optional[str], Optional[str]]:
    """Renders the partner selection and info header."""
    partners = sorted(
        [str(p) for p in dados_df[C.COL_INT_PARTNER].unique() if p and str(p).strip()]
    )

    if not partners:
        st.warning(C.UI_LABEL_NO_PARTNERS_FOUND)
        return None, None, None, None

    col_sel, col_info = st.columns([1, 2])

    with col_sel:
        selected_partner = st.selectbox("Selecione o Parceiro", partners)

    partner_data = dados_df[dados_df[C.COL_INT_PARTNER] == selected_partner]
    if partner_data.empty:
        st.error("Dados do parceiro não encontrados.")
        return None, None, None, None

    city, state = _get_base_location(partner_data)

    with col_info:
        st.markdown(f"### {selected_partner}")
        st.markdown(f" **Localização Base:** {city} - {state}")
        st.markdown(f" **Total de Contratos:** {len(partner_data)}")

    st.divider()
    return selected_partner, partner_data, city, state


def render(
    dados_df: pd.DataFrame,
    build_oportunidade_por_uf: Callable[[pd.DataFrame, List[str]], pd.DataFrame],
    access_key: str,
):
    st.header(C.TAB_NAME_UNIT_ANALYSIS)

    if not _check_authentication(access_key):
        return

    # --- Main Content ---

    # 1. Partner Selection & Header
    selected_partner, partner_data, city, state = _render_partner_header(dados_df)
    if not selected_partner or not city or not state:
        return

    # 2. AI Analysis Trigger
    st.markdown("####  Inteligência de Mercado")
    st.write(
        "Utilize nossa IA para cruzar dados geográficos, demográficos e de contratos para gerar insights personalizados."
    )

    if st.button("✨ Gerar Análise Unitária (IA)"):
        _run_ai_analysis(city, state, dados_df, build_oportunidade_por_uf, GeocodingService())



