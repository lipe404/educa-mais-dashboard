import streamlit as st
import pandas as pd
import plotly.express as px
import os
from dotenv import load_dotenv
import constants as C

load_dotenv()
API_KEY = os.getenv("KEY_API")


def render(students_df: pd.DataFrame):
    key = st.text_input(C.UI_LABEL_ACCESS_KEY,
                        type="password", key="students_access_key")
    if key != API_KEY:
        st.warning(C.UI_LABEL_ENTER_KEY_MSG)
        return

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
