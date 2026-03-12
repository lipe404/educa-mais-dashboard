import streamlit as st
import pandas as pd
import plotly.express as px
import constants as C
from typing import Callable, Tuple, Optional
from datetime import datetime
import math
from geocoding_service import GeocodingService


def _filter_students_data(students_df: pd.DataFrame) -> pd.DataFrame:
    """
    Filters and cleans students data for analysis.
    
    Removes 'POS' financial types, splits multiple courses, cleans course names,
    and removes invalid entries.

    Args:
        students_df (pd.DataFrame): Raw dataframe containing student data.

    Returns:
        pd.DataFrame: Cleaned and filtered dataframe ready for analysis.
    """
    if students_df.empty:
        return pd.DataFrame()

    filtered_df = students_df.copy()

    # Ensure financial type is string and upper for comparison
    filtered_df[C.COL_INT_FINANCIAL_TYPE] = (
        filtered_df[C.COL_INT_FINANCIAL_TYPE].astype(str).str.upper()
    )

    # Filter logic: Keep only what is NOT 'POS'
    mask_pos = filtered_df[C.COL_INT_FINANCIAL_TYPE].str.contains(
        "POS|PÓS", case=False, na=False
    )
    filtered_df = filtered_df[~mask_pos]

    if filtered_df.empty:
        return pd.DataFrame()

    # Split multiple courses in the same cell (separated by ';')
    filtered_df[C.COL_INT_COURSE] = (
        filtered_df[C.COL_INT_COURSE].astype(str).str.split(";")
    )
    filtered_df = filtered_df.explode(C.COL_INT_COURSE)

    # Clean up course names
    filtered_df[C.COL_INT_COURSE] = (
        filtered_df[C.COL_INT_COURSE]
        .astype(str)
        .str.upper()
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
    )

    # Filter out invalid course names
    mask_valid_course = ~filtered_df[C.COL_INT_COURSE].isin(
        ["NAN", "NONE", "", "CURSO NÃO IDENTIFICADO"]
    )
    filtered_df = filtered_df[mask_valid_course]

    return filtered_df


def _render_top_courses_chart(filtered_df: pd.DataFrame) -> None:
    """
    Renders a bar chart showing the top 10 most sold courses.

    Args:
        filtered_df (pd.DataFrame): Filtered dataframe containing student course data.
    """
    st.markdown("#### Cursos Mais Vendidos")

    course_counts = filtered_df[C.COL_INT_COURSE].value_counts().reset_index()
    course_counts.columns = [C.COL_INT_COURSE, "Quantidade"]

    # Limit to Top 10 courses
    top_courses = course_counts.head(10)

    fig_courses = px.bar(
        top_courses,
        x="Quantidade",
        y=C.COL_INT_COURSE,
        orientation="h",
        title="Top 10 Cursos Mais Vendidos",
        text_auto=True,
        color="Quantidade",
        color_continuous_scale=px.colors.sequential.Viridis,
    )
    fig_courses.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig_courses, width="stretch")
    st.divider()


def _render_partner_courses_chart(filtered_df: pd.DataFrame) -> None:
    """
    Renders a stacked bar chart showing course sales distribution by partner.

    Args:
        filtered_df (pd.DataFrame): Filtered dataframe containing student course data.
    """
    st.markdown("#### Cursos Mais Vendidos por Parceiro")

    partner_counts = (
        filtered_df.groupby([C.COL_INT_PARTNER, C.COL_INT_COURSE])
        .size()
        .reset_index(name="Quantidade")
    )

    # Get Top 20 partners by total quantity
    top_partners = (
        partner_counts.groupby(C.COL_INT_PARTNER)["Quantidade"]
        .sum()
        .sort_values(ascending=False)
        .head(20)
        .index
    )

    filtered_partner_counts = partner_counts[
        partner_counts[C.COL_INT_PARTNER].isin(top_partners)
    ]

    fig_partner_courses = px.bar(
        filtered_partner_counts,
        x=C.COL_INT_PARTNER,
        y="Quantidade",
        color=C.COL_INT_COURSE,
        title="Top Cursos por Parceiro (Top 20 Parceiros)",
        labels={
            C.COL_INT_PARTNER: "Parceiro",
            "Quantidade": "Vendas",
            C.COL_INT_COURSE: "Curso",
        },
        barmode="stack",
    )
    fig_partner_courses.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_partner_courses, width="stretch")
    st.divider()


def _render_raw_data_expander(filtered_df: pd.DataFrame) -> None:
    """
    Renders an expander containing the raw data table for detailed inspection.

    Args:
        filtered_df (pd.DataFrame): Filtered dataframe to be displayed.
    """
    with st.expander("Ver dados detalhados"):
        show_table = st.checkbox(
            "Carregar tabela paginada",
            value=False,
            key="students_analysis_raw_show_table",
        )
        if not show_table:
            return

        cols = [
            C.COL_INT_PARTNER,
            C.COL_INT_STUDENT_NAME,
            C.COL_INT_COURSE,
            C.COL_INT_FINANCIAL_TYPE,
            C.COL_INT_DATA,
        ]
        table_df = filtered_df[cols].reset_index(drop=True)

        page_size = st.selectbox(
            "Linhas por página",
            options=[50, 100, 200, 500],
            index=1,
            key="students_analysis_raw_page_size",
        )
        total_rows = len(table_df)
        total_pages = max(1, math.ceil(total_rows / page_size)) if page_size else 1

        page = st.number_input(
            "Página",
            min_value=1,
            max_value=total_pages,
            value=min(
                int(st.session_state.get("students_analysis_raw_page", 1)), total_pages
            ),
            step=1,
            key="students_analysis_raw_page",
        )

        start = (page - 1) * page_size
        end = min(start + page_size, total_rows)

        st.caption(f"Mostrando linhas {start + 1}-{end} de {total_rows}")
        st.data_editor(
            table_df.iloc[start:end],
            use_container_width=True,
            hide_index=True,
            disabled=True,
            key="students_analysis_raw_editor",
        )


def _render_analysis_tab(students_df: pd.DataFrame) -> None:
    """
    Renders the Students Analysis sub-tab (Course Analysis).

    Args:
        students_df (pd.DataFrame): Raw dataframe containing student data.
    """
    st.markdown("### Análise de Alunos e Cursos")

    if students_df.empty:
        st.info("Nenhum dado de alunos disponível.")
        return

    filtered_df = _filter_students_data(students_df)

    if filtered_df.empty:
        st.info(
            "Nenhum dado encontrado após aplicar o filtro (removendo Pós-Graduação e cursos inválidos)."
        )
        return

    _render_top_courses_chart(filtered_df)
    _render_partner_courses_chart(filtered_df)
    _render_raw_data_expander(filtered_df)


def _render_general_metrics(df: pd.DataFrame) -> None:
    """
    Renders general metrics cards (Total Students, Cities, States).

    Args:
        df (pd.DataFrame): Dataframe containing general student data.
    """
    total_students = len(df)
    unique_cities = df[C.COL_INT_GEN_CITY].nunique()
    unique_states = df[C.COL_INT_GEN_STATE].nunique()

    c1, c2, c3 = st.columns(3)
    c1.metric("Total de Alunos", total_students)
    c2.metric("Cidades Atendidas", unique_cities)
    c3.metric("Estados Atendidos", unique_states)
    st.divider()


def _render_general_charts(df: pd.DataFrame) -> None:
    """
    Renders charts for the General Data tab including state, city, and regional distribution.

    Args:
        df (pd.DataFrame): Dataframe containing general student data.
    """
    # 1. States with most students
    st.markdown("#### Estados com mais Alunos")
    state_counts = df[C.COL_INT_GEN_STATE].value_counts().reset_index()
    state_counts.columns = ["Estado", "Quantidade"]

    fig_states = px.bar(
        state_counts,
        x="Estado",
        y="Quantidade",
        title="Distribuição de Alunos por Estado",
        text_auto=True,
        color="Quantidade",
        color_continuous_scale="Blues",
    )
    st.plotly_chart(fig_states, width="stretch")
    st.divider()

    # 2. Cities with most students
    st.markdown("#### Top 10 Cidades com mais Alunos")
    city_counts = df[C.COL_INT_GEN_CITY].value_counts().head(10).reset_index()
    city_counts.columns = ["Cidade", "Quantidade"]

    fig_cities = px.bar(
        city_counts,
        x="Quantidade",
        y="Cidade",
        orientation="h",
        title="Top 10 Cidades",
        text_auto=True,
        color="Quantidade",
        color_continuous_scale="Greens",
    )
    fig_cities.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig_cities, width="stretch")
    st.divider()

    # 3. Regions with most students
    st.markdown("#### Alunos por Região")
    if C.COL_INT_REGION in df.columns:
        region_counts = df[C.COL_INT_REGION].value_counts().reset_index()
        region_counts.columns = ["Região", "Quantidade"]

        fig_regions = px.pie(
            region_counts,
            values="Quantidade",
            names="Região",
            title="Distribuição Regional",
            hole=0.4,
        )
        st.plotly_chart(fig_regions, width="stretch")
    else:
        st.warning("Informação de região não disponível.")
    st.divider()


def _render_geo_distribution_map(df: pd.DataFrame) -> None:
    """Renders the geographic distribution map."""
    st.markdown("#### Distribuição Geográfica (Mapa de Pontos)")

    if C.COL_INT_GEN_ZIP not in df.columns:
        st.warning("Coluna de CEP não encontrada.")
        st.divider()
        return

    # Checkbox to enable map generation
    if not st.checkbox("Gerar Mapa de Distribuição (Baseado no CEP)"):
        st.divider()
        return

    geo_service = GeocodingService()

    # Extract unique ZIPs and counts
    zip_counts = df[C.COL_INT_GEN_ZIP].value_counts().reset_index()
    zip_counts.columns = ["cep", "count"]

    total_zips = len(zip_counts)
    st.info(
        f"Total de CEPs únicos encontrados: {total_zips}. A geocodificação pode demorar se não estiver em cache."
    )

    # Progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    coords_data = []

    for i, row in zip_counts.iterrows():
        cep = row["cep"]
        count = row["count"]
        status_text.text(f"Processando CEP: {cep} ({i+1}/{len(zip_counts)})")

        lat, lon = geo_service.get_coords_by_zip(cep)
        if lat is not None and lon is not None:
            coords_data.append(
                {"lat": lat, "lon": lon, "cep": cep, "alunos": count}
            )

        progress_bar.progress((i + 1) / len(zip_counts))

    progress_bar.empty()
    status_text.empty()

    if coords_data:
        map_df = pd.DataFrame(coords_data)

        # Using Plotly Scatter Mapbox
        fig_map = px.scatter_mapbox(
            map_df,
            lat="lat",
            lon="lon",
            size="alunos",
            hover_name="cep",
            hover_data={"alunos": True, "lat": False, "lon": False},
            color_discrete_sequence=["blue"],
            zoom=3,
            height=500,
            size_max=15,
        )
        fig_map.update_layout(mapbox_style="open-street-map")
        fig_map.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

        st.plotly_chart(fig_map, width="stretch")
    else:
        st.warning(
            "Não foi possível obter coordenadas para os CEPs fornecidos."
        )
    st.divider()


def _render_general_tab(
    sheet_id: str, fetch_data: Callable[[str], Tuple[pd.DataFrame, datetime]]
) -> None:
    """
    Renders the General Data sub-tab.

    Args:
        sheet_id (str): The Google Sheets ID to fetch data from.
        fetch_data (Callable): Function to fetch general student data.
    """
    st.markdown("### Dados Gerais de Alunos")

    with st.spinner("Carregando dados gerais de alunos..."):
        df, ts = fetch_data(sheet_id)

    if df.empty:
        st.warning("Não foi possível carregar os dados gerais de alunos.")
        return

    _render_general_metrics(df)
    _render_general_charts(df)
    _render_geo_distribution_map(df)

    # Show raw data option
    with st.expander("Visualizar Dados Brutos (ALUNOS_GERAL)"):
        show_table = st.checkbox(
            "Carregar tabela paginada",
            value=False,
            key="students_general_raw_show_table",
        )
        if not show_table:
            return

        table_df = df.reset_index(drop=True)
        page_size = st.selectbox(
            "Linhas por página",
            options=[50, 100, 200, 500],
            index=1,
            key="students_general_raw_page_size",
        )
        total_rows = len(table_df)
        total_pages = max(1, math.ceil(total_rows / page_size)) if page_size else 1

        page = st.number_input(
            "Página",
            min_value=1,
            max_value=total_pages,
            value=min(
                int(st.session_state.get("students_general_raw_page", 1)), total_pages
            ),
            step=1,
            key="students_general_raw_page",
        )

        start = (page - 1) * page_size
        end = min(start + page_size, total_rows)

        st.caption(f"Mostrando linhas {start + 1}-{end} de {total_rows}")
        st.data_editor(
            table_df.iloc[start:end],
            use_container_width=True,
            hide_index=True,
            disabled=True,
            key="students_general_raw_editor",
        )


def render(
    students_df: pd.DataFrame,
    fetch_general_data: Callable[[str], Tuple[pd.DataFrame, datetime]],
    access_key: str,
    sheet_id: str = None,
) -> None:
    """
    Main render function for the Students Tab.

    Args:
        students_df (pd.DataFrame): Raw dataframe containing student data.
        fetch_general_data (Callable): Function to fetch general student data.
        access_key (str): The access key required to view sensitive data.
        sheet_id (str, optional): The Google Sheets ID. Defaults to None.
    """
    key = st.text_input(
        C.UI_LABEL_ACCESS_KEY, type="password", key="students_access_key"
    )
    if key != access_key:
        st.warning(C.UI_LABEL_ENTER_KEY_MSG)
        return

    # Sub-navigation
    view_mode = st.radio(
        "Selecione a visualização:",
        ["Análise de Cursos (Planilha Alunos)", "Dados Gerais (Planilha ALUNOS_GERAL)"],
        horizontal=True,
    )

    st.divider()

    if view_mode == "Análise de Cursos (Planilha Alunos)":
        _render_analysis_tab(students_df)
    else:
        if sheet_id:
            _render_general_tab(sheet_id, fetch_general_data)
        else:
            st.error(
                "ID da planilha não configurado. Verifique as variáveis de ambiente."
            )
