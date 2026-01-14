import streamlit as st
import pandas as pd
import plotly.express as px
import os
from dotenv import load_dotenv
import constants as C
from services import data as data_service

load_dotenv()
API_KEY = os.getenv("KEY_API")


def render_analysis(students_df: pd.DataFrame):
    st.markdown("### Análise de Alunos e Cursos")

    if students_df.empty:
        st.info("Nenhum dado de alunos disponível.")
        return

    # Filter out POS
    # User requested: "descarte tudo que esteja em POS"
    # Assuming 'POS' is in C.COL_INT_FINANCIAL_TYPE
    # We should normalize comparison to be safe (upper case)
    
    filtered_df = students_df.copy()
    
    # Ensure financial type is string and upper for comparison
    filtered_df[C.COL_INT_FINANCIAL_TYPE] = filtered_df[C.COL_INT_FINANCIAL_TYPE].astype(str).str.upper()
    
    # Filter logic: Keep only what is NOT 'POS' (or strictly keep 'TECNICO' if that was the requirement)
    # Broader check for any variation of POS/PÓS
    mask_pos = filtered_df[C.COL_INT_FINANCIAL_TYPE].str.contains("POS|PÓS", case=False, na=False)
    filtered_df = filtered_df[~mask_pos]

    if filtered_df.empty:
        st.info("Nenhum dado encontrado após aplicar o filtro (removendo Pós-Graduação).")
        return

    # Split multiple courses in the same cell (separated by ';')
    filtered_df[C.COL_INT_COURSE] = filtered_df[C.COL_INT_COURSE].astype(str).str.split(';')
    filtered_df = filtered_df.explode(C.COL_INT_COURSE)

    # Clean up course names
    # Ensure it's string, uppercase, strip whitespace, and normalize internal spaces
    filtered_df[C.COL_INT_COURSE] = filtered_df[C.COL_INT_COURSE].astype(str).str.upper().str.strip().str.replace(r'\s+', ' ', regex=True)

    # Filter out invalid course names (nan, empty, etc.)
    # The user explicitly wants to remove empty/nan lines
    mask_valid_course = ~filtered_df[C.COL_INT_COURSE].isin(["NAN", "NONE", "", "CURSO NÃO IDENTIFICADO"])
    filtered_df = filtered_df[mask_valid_course]

    if filtered_df.empty:
        st.info("Nenhum dado válido de cursos encontrado após limpeza.")
        return

    # --- Chart 1: Cursos mais vendidos ---
    st.markdown("#### Cursos Mais Vendidos")
    
    course_counts = filtered_df[C.COL_INT_COURSE].value_counts().reset_index()
    course_counts.columns = [C.COL_INT_COURSE, "Quantidade"]
    
    # Limit to Top 10 courses to avoid clutter if there are many
    top_courses = course_counts.head(10)

    fig_courses = px.bar(
        top_courses,
        x="Quantidade",
        y=C.COL_INT_COURSE,
        orientation='h',
        title="Top 10 Cursos Mais Vendidos",
        text_auto=True,
        color="Quantidade",
        color_continuous_scale=px.colors.sequential.Viridis
    )
    fig_courses.update_layout(yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig_courses, width="stretch")

    # --- Chart 2: Cursos mais vendidos por parceiros ---
    st.markdown("#### Cursos Mais Vendidos por Parceiro")
    
    # Group by Partner and Course
    # We might want to filter partners with very few sales to keep chart clean?
    # Or show all. Let's try showing top 20 partners by volume first if too many.
    
    partner_counts = filtered_df.groupby([C.COL_INT_PARTNER, C.COL_INT_COURSE]).size().reset_index(name="Quantidade")
    
    # Get Top N partners by total quantity to sort the axis
    top_partners = partner_counts.groupby(C.COL_INT_PARTNER)["Quantidade"].sum().sort_values(ascending=False).head(20).index
    
    filtered_partner_counts = partner_counts[partner_counts[C.COL_INT_PARTNER].isin(top_partners)]
    
    fig_partner_courses = px.bar(
        filtered_partner_counts,
        x=C.COL_INT_PARTNER,
        y="Quantidade",
        color=C.COL_INT_COURSE,
        title="Top Cursos por Parceiro (Top 20 Parceiros)",
        labels={C.COL_INT_PARTNER: "Parceiro", "Quantidade": "Vendas", C.COL_INT_COURSE: "Curso"},
        barmode="stack"
    )
    fig_partner_courses.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_partner_courses, width="stretch")
    
    # Raw Data Expander
    with st.expander("Ver dados detalhados"):
        st.dataframe(filtered_df[[
            C.COL_INT_PARTNER, 
            C.COL_INT_STUDENT_NAME, 
            C.COL_INT_COURSE, 
            C.COL_INT_FINANCIAL_TYPE,
            C.COL_INT_DATA
        ]])


def render_general(sheet_id: str):
    st.markdown("### Dados Gerais de Alunos")
    
    with st.spinner("Carregando dados gerais de alunos..."):
        df = data_service.get_students_general_data(sheet_id)
        
    if df.empty:
        st.warning("Não foi possível carregar os dados gerais de alunos.")
        return

    # Metrics
    total_students = len(df)
    unique_cities = df[C.COL_INT_GEN_CITY].nunique()
    unique_states = df[C.COL_INT_GEN_STATE].nunique()
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Total de Alunos", total_students)
    c2.metric("Cidades Atendidas", unique_cities)
    c3.metric("Estados Atendidos", unique_states)
    
    st.divider()

    # 1. Estados com mais alunos
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
        color_continuous_scale="Blues"
    )
    st.plotly_chart(fig_states, use_container_width=True)
    
    # 2. Cidades com mais alunos
    st.markdown("#### Top 10 Cidades com mais Alunos")
    city_counts = df[C.COL_INT_GEN_CITY].value_counts().head(10).reset_index()
    city_counts.columns = ["Cidade", "Quantidade"]
    
    fig_cities = px.bar(
        city_counts,
        x="Quantidade",
        y="Cidade",
        orientation='h',
        title="Top 10 Cidades",
        text_auto=True,
        color="Quantidade",
        color_continuous_scale="Greens"
    )
    fig_cities.update_layout(yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig_cities, use_container_width=True)

    # 3. Regiões com mais alunos
    st.markdown("#### Alunos por Região")
    if C.COL_INT_REGION in df.columns:
        region_counts = df[C.COL_INT_REGION].value_counts().reset_index()
        region_counts.columns = ["Região", "Quantidade"]
        
        fig_regions = px.pie(
            region_counts,
            values="Quantidade",
            names="Região",
            title="Distribuição Regional",
            hole=0.4
        )
        st.plotly_chart(fig_regions, use_container_width=True)
    else:
        st.warning("Informação de região não disponível.")

    # Show raw data option
    with st.expander("Visualizar Dados Brutos (ALUNOS_GERAL)"):
        st.dataframe(df)


def render(students_df: pd.DataFrame, sheet_id: str = None):
    key = st.text_input(C.UI_LABEL_ACCESS_KEY,
                        type="password", key="students_access_key")
    if key != API_KEY:
        st.warning(C.UI_LABEL_ENTER_KEY_MSG)
        return

    # Sub-navigation
    view_mode = st.radio(
        "Selecione a visualização:",
        ["Análise de Cursos (Planilha Alunos)", "Dados Gerais (Planilha ALUNOS_GERAL)"],
        horizontal=True
    )
    
    st.divider()

    if view_mode == "Análise de Cursos (Planilha Alunos)":
        render_analysis(students_df)
    else:
        if sheet_id:
            render_general(sheet_id)
        else:
            st.error("ID da planilha não configurado. Verifique as variáveis de ambiente.")
