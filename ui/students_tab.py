import streamlit as st
import pandas as pd
import plotly.express as px
import constants as C
from typing import Callable, Tuple, Optional
from datetime import datetime
import math
from geocoding_service import GeocodingService
import unicodedata


def _normalize_text(value: str) -> str:
    if not isinstance(value, str):
        return ""
    value = (
        "".join(
            ch
            for ch in unicodedata.normalize("NFD", value)
            if unicodedata.category(ch) != "Mn"
        )
        .upper()
        .strip()
    )
    return " ".join(value.split())


def _build_student_id_series(df: pd.DataFrame) -> pd.Series:
    if df.empty:
        return pd.Series(dtype="object")

    name_series = pd.Series("", index=df.index, dtype="object")
    if C.COL_INT_STUDENT_NAME in df.columns:
        name_series = (
            df[C.COL_INT_STUDENT_NAME].astype(str).str.strip().str.lower()
        )

    if C.COL_INT_CPF not in df.columns:
        return name_series

    cpf_series = (
        df[C.COL_INT_CPF].astype(str).str.replace(r"\D+", "", regex=True).str.strip()
    )
    cpf_valid = cpf_series.str.len() >= 11
    return cpf_series.where(cpf_valid, name_series)


def _render_type_pie_chart(students_df: pd.DataFrame) -> None:
    if students_df.empty or C.COL_INT_FINANCIAL_TYPE not in students_df.columns:
        return

    tmp = students_df[[C.COL_INT_FINANCIAL_TYPE]].copy()
    tmp["Tipo"] = (
        tmp[C.COL_INT_FINANCIAL_TYPE]
        .astype(str)
        .str.strip()
        .str.upper()
        .replace({"": pd.NA, "NAN": pd.NA, "NONE": pd.NA})
    )

    if C.COL_INT_COURSE in students_df.columns:
        eja_targets = {
            _normalize_text(
                "EDUCAÇÃO DE JOVENS E ADULTOS À DISTÂNCIA - ENSINO FUNDAMENTAL"
            ),
            _normalize_text("EDUCAÇÃO DE JOVENS E ADULTOS À DISTÂNCIA - ENSINO MÉDIO"),
        }
        course_norm = students_df[C.COL_INT_COURSE].astype(str).map(_normalize_text)
        tmp.loc[course_norm.isin(eja_targets), "Tipo"] = "EJA"

    types = tmp["Tipo"].dropna()
    if types.empty:
        return

    counts = types.value_counts()
    top_n = 8
    if len(counts) > top_n:
        top = counts.head(top_n)
        others = int(counts.iloc[top_n:].sum())
        pie_df = top.reset_index()
        pie_df.columns = ["Tipo", "Quantidade"]
        pie_df = pd.concat(
            [pie_df, pd.DataFrame([{"Tipo": "OUTROS", "Quantidade": others}])],
            ignore_index=True,
        )
    else:
        pie_df = counts.reset_index()
        pie_df.columns = ["Tipo", "Quantidade"]

    st.markdown("#### Tipos Mais Vendidos (TIPO)")
    fig = px.pie(
        pie_df,
        names="Tipo",
        values="Quantidade",
        title="Distribuição de Vendas por Tipo",
        hole=0.35,
    )
    st.plotly_chart(fig, width="stretch")
    st.divider()


def _find_column(df: pd.DataFrame, primary: str, aliases: list[str]) -> str | None:
    if primary in df.columns:
        return primary
    for a in aliases:
        if a in df.columns:
            return a
    primary_u = str(primary).strip().upper()
    aliases_u = {str(a).strip().upper() for a in aliases}
    for col in df.columns:
        col_u = str(col).strip().upper()
        if col_u == primary_u or col_u in aliases_u:
            return col
    return None


def _normalize_person_name_series(s: pd.Series) -> pd.Series:
    if s is None:
        return pd.Series(dtype="object")
    return s.astype(str).map(_normalize_text)


def _build_students_sales_lookup(students_df: pd.DataFrame) -> pd.DataFrame:
    if students_df.empty:
        return pd.DataFrame(
            columns=["_k_partner", "_k_day", "_k_name", "curso", "tipo"]
        )

    needed = [C.COL_INT_PARTNER, C.COL_INT_DATA, C.COL_INT_STUDENT_NAME, C.COL_INT_COURSE]
    missing = [c for c in needed if c not in students_df.columns]
    if missing:
        return pd.DataFrame(
            columns=["_k_partner", "_k_day", "_k_name", "curso", "tipo"]
        )

    base = students_df[needed + ([C.COL_INT_FINANCIAL_TYPE] if C.COL_INT_FINANCIAL_TYPE in students_df.columns else [])].copy()
    base = base[base[C.COL_INT_PARTNER].notna() & base[C.COL_INT_DATA].notna()]
    base = base[base[C.COL_INT_STUDENT_NAME].notna() & base[C.COL_INT_COURSE].notna()]
    if base.empty:
        return pd.DataFrame(
            columns=["_k_partner", "_k_day", "_k_name", "curso", "tipo"]
        )

    base["_k_partner"] = base[C.COL_INT_PARTNER].astype(str).str.strip()
    base["_k_day"] = pd.to_datetime(base[C.COL_INT_DATA].dt.date)
    base["_k_name"] = _normalize_person_name_series(base[C.COL_INT_STUDENT_NAME])

    course_norm = base[C.COL_INT_COURSE].astype(str).map(_normalize_text)
    eja_targets = {
        _normalize_text(
            "EDUCAÇÃO DE JOVENS E ADULTOS À DISTÂNCIA - ENSINO FUNDAMENTAL"
        ),
        _normalize_text("EDUCAÇÃO DE JOVENS E ADULTOS À DISTÂNCIA - ENSINO MÉDIO"),
    }
    is_eja = course_norm.isin(eja_targets)

    base["curso"] = (
        base[C.COL_INT_COURSE].astype(str).str.strip().str.upper().replace({"": pd.NA})
    )
    base.loc[is_eja, "curso"] = "EJA"

    if C.COL_INT_FINANCIAL_TYPE in base.columns:
        base["tipo"] = (
            base[C.COL_INT_FINANCIAL_TYPE]
            .astype(str)
            .str.strip()
            .str.upper()
            .replace({"": pd.NA, "NAN": pd.NA, "NONE": pd.NA})
        )
    else:
        base["tipo"] = pd.NA

    base.loc[is_eja, "tipo"] = "EJA"

    def _mode_or_na(s: pd.Series):
        s = s.dropna()
        if s.empty:
            return pd.NA
        return s.mode().iloc[0] if not s.mode().empty else s.iloc[0]

    lookup = (
        base.groupby(["_k_partner", "_k_day", "_k_name"], dropna=True)
        .agg(curso=("curso", _mode_or_na), tipo=("tipo", _mode_or_na))
        .reset_index()
    )
    lookup = lookup[(lookup["_k_partner"] != "") & (lookup["_k_name"] != "")]
    return lookup


def _render_ticket_breakdowns(
    faturamento_df: pd.DataFrame, students_df: pd.DataFrame
) -> None:
    if faturamento_df.empty:
        return
    if C.COL_INT_VALOR not in faturamento_df.columns:
        return

    df = faturamento_df.copy()
    df = df[df[C.COL_INT_VALOR].notna()]
    if df.empty:
        return
    df = df.reset_index(drop=True)

    tipo_col = C.COL_INT_FINANCIAL_TYPE if C.COL_INT_FINANCIAL_TYPE in df.columns else None
    partner_col = C.COL_INT_PARTNER if C.COL_INT_PARTNER in df.columns else None
    date_col = C.COL_INT_DATA if C.COL_INT_DATA in df.columns else None

    if tipo_col:
        df[tipo_col] = (
            df[tipo_col].astype(str).str.strip().str.upper().replace({"": pd.NA})
        )

    if partner_col:
        df[partner_col] = (
            df[partner_col].astype(str).str.strip().replace({"": pd.NA})
        )

    resolved_course_col = None
    maybe_course_col = (
        C.COL_INT_COURSE
        if C.COL_INT_COURSE in df.columns
        else _find_column(df, C.COL_SRC_COURSE, ["Curso", "CURSO", "curso"])
    )

    if maybe_course_col:
        df[maybe_course_col] = (
            df[maybe_course_col].astype(str).str.strip().str.upper().replace({"": pd.NA})
        )

        if df[maybe_course_col].notna().any():
            resolved_course_col = maybe_course_col
            course_norm = df[resolved_course_col].astype(str).map(_normalize_text)
            eja_targets = {
                _normalize_text(
                    "EDUCAÇÃO DE JOVENS E ADULTOS À DISTÂNCIA - ENSINO FUNDAMENTAL"
                ),
                _normalize_text("EDUCAÇÃO DE JOVENS E ADULTOS À DISTÂNCIA - ENSINO MÉDIO"),
            }
            is_eja_course = course_norm.isin(eja_targets)
            if tipo_col:
                df.loc[is_eja_course, tipo_col] = "EJA"
            df.loc[is_eja_course, resolved_course_col] = "EJA"

    if not resolved_course_col:
        lookup = _build_students_sales_lookup(students_df)
        if (
            not lookup.empty
            and partner_col
            and date_col
            and df[partner_col].notna().any()
            and df[date_col].notna().any()
        ):
            faturamento_name_col = _find_column(
                df,
                C.COL_INT_STUDENT_NAME,
                [
                    C.COL_SRC_STUDENT_NAME,
                    "NOME DO ALUNO",
                    "Nome do Aluno",
                    "Nome",
                    "NOME",
                    "Aluno",
                    "ALUNO",
                ],
            )

            df["_k_partner"] = df[partner_col].astype(str).str.strip()
            df["_k_day"] = pd.to_datetime(df[date_col].dt.date)

            if faturamento_name_col:
                df["_k_name"] = _normalize_person_name_series(df[faturamento_name_col])
                df = df.merge(
                    lookup,
                    on=["_k_partner", "_k_day", "_k_name"],
                    how="left",
                )
            else:
                day_lookup = (
                    lookup.groupby(["_k_partner", "_k_day"], dropna=True)
                    .agg(
                        n_cursos=("curso", lambda s: s.dropna().nunique()),
                        curso=("curso", lambda s: s.dropna().unique().tolist()),
                        tipo=("tipo", lambda s: s.dropna().unique().tolist()),
                    )
                    .reset_index()
                )
                df = df.merge(day_lookup, on=["_k_partner", "_k_day"], how="left")
                df["curso"] = df["curso"].apply(
                    lambda v: (v[0] if isinstance(v, list) and len(v) == 1 else pd.NA)
                )
                df["tipo"] = df["tipo"].apply(
                    lambda v: (v[0] if isinstance(v, list) and len(v) == 1 else pd.NA)
                )

            resolved_course_col = "curso"
            if tipo_col:
                df[tipo_col] = df["tipo"].where(
                    df["tipo"].notna(), df[tipo_col]
                )

    def build_group(dim_col: str) -> pd.DataFrame:
        g = (
            df[df[dim_col].notna()]
            .groupby(dim_col, dropna=True)[C.COL_INT_VALOR]
            .agg(vendas="count", faturamento="sum", ticket_medio="mean")
            .reset_index()
        )
        g = g.sort_values(["ticket_medio", "vendas"], ascending=[False, False])
        return g

    st.markdown("#### Ticket Médio por Segmento")
    c1, c2, c3 = st.columns(3)

    with c1:
        if resolved_course_col:
            g = build_group(resolved_course_col).head(15)
            g = g.rename(columns={resolved_course_col: "Curso"})
            if g.empty:
                st.info("Não foi possível vincular cursos ao faturamento com as chaves atuais.")
            else:
                fig = px.bar(
                    g,
                    x="ticket_medio",
                    y="Curso",
                    orientation="h",
                    title="Por Curso (Top 15)",
                    hover_data={"vendas": True, "faturamento": ":,.2f", "ticket_medio": ":,.2f"},
                )
                fig.update_yaxes(categoryorder="total ascending")
                fig.update_xaxes(title="R$")
                st.plotly_chart(fig, width="stretch")
        else:
            st.info("Curso indisponível: faltam dados para vincular FATURAMENTO aos cursos (ALUNOS).")

    with c2:
        if tipo_col:
            g = build_group(tipo_col)
            g = g.rename(columns={tipo_col: "Tipo"})
            if g.empty:
                st.info("Sem dados suficientes para calcular ticket por tipo.")
            else:
                def _fmt_brl(v: float) -> str:
                    try:
                        s = f"{float(v):,.2f}"
                    except Exception:
                        return "R$ 0,00"
                    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
                    return f"R$ {s}"

                def _fmt_int(v: float) -> str:
                    try:
                        return f"{int(v):,}".replace(",", ".")
                    except Exception:
                        return "0"

                g["label"] = g.apply(
                    lambda r: (
                        f"Ticket: {_fmt_brl(r['ticket_medio'])}"
                        f"<br>Vendas: {_fmt_int(r['vendas'])}"
                        f"<br>Fat: {_fmt_brl(r['faturamento'])}"
                    ),
                    axis=1,
                )
                fig = px.bar(
                    g,
                    x="ticket_medio",
                    y="Tipo",
                    orientation="h",
                    title="Por Tipo",
                    hover_data={"vendas": True, "faturamento": ":,.2f", "ticket_medio": ":,.2f"},
                    text="label",
                )
                fig.update_traces(texttemplate="%{text}", textposition="auto")
                fig.update_yaxes(categoryorder="total ascending")
                fig.update_xaxes(title="R$")
                st.plotly_chart(fig, width="stretch")
        else:
            st.info("Tipo não disponível no faturamento.")

    with c3:
        if partner_col:
            g = build_group(partner_col).head(20)
            g = g.rename(columns={partner_col: "Parceiro"})
            if g.empty:
                st.info("Sem dados suficientes para calcular ticket por parceiro.")
            else:
                fig = px.bar(
                    g,
                    x="ticket_medio",
                    y="Parceiro",
                    orientation="h",
                    title="Por Parceiro (Top 20)",
                    hover_data={"vendas": True, "faturamento": ":,.2f", "ticket_medio": ":,.2f"},
                )
                fig.update_yaxes(categoryorder="total ascending")
                fig.update_xaxes(title="R$")
                st.plotly_chart(fig, width="stretch")
        else:
            st.info("Parceiro não disponível no faturamento.")

    st.divider()


def _render_ticket_and_students_timeseries(
    filtered_df: pd.DataFrame, faturamento_df: pd.DataFrame | None
) -> None:
    if faturamento_df is not None and not faturamento_df.empty:
        if (
            C.COL_INT_DATA in faturamento_df.columns
            and C.COL_INT_VALOR in faturamento_df.columns
        ):
            df_f = faturamento_df[[C.COL_INT_DATA, C.COL_INT_VALOR]].copy()
            df_f = df_f[df_f[C.COL_INT_DATA].notna() & df_f[C.COL_INT_VALOR].notna()]
            if not df_f.empty:
                df_f["Dia"] = pd.to_datetime(df_f[C.COL_INT_DATA].dt.date)
                daily_f = (
                    df_f.groupby("Dia")
                    .agg(qtd=(C.COL_INT_VALOR, "count"), soma=(C.COL_INT_VALOR, "sum"))
                    .reset_index()
                    .sort_values("Dia")
                )
                daily_f["ticket_medio"] = (
                    daily_f["soma"].cumsum() / daily_f["qtd"].cumsum()
                ).fillna(0.0)

                st.markdown("#### Ticket Médio ao Longo do Tempo")
                fig_ticket = px.line(
                    daily_f,
                    x="Dia",
                    y="ticket_medio",
                    title="Ticket Médio (Média Acumulada)",
                    markers=True,
                )
                fig_ticket.update_yaxes(title="R$")
                st.plotly_chart(fig_ticket, width="stretch")
                st.divider()
                _render_ticket_breakdowns(faturamento_df, filtered_df)
        else:
            st.info("Ticket médio indisponível: faltam colunas de data/valor no faturamento.")
    else:
        st.info("Ticket médio indisponível: faturamento vazio ou não fornecido.")

    if (
        filtered_df.empty
        or C.COL_INT_DATA not in filtered_df.columns
        or C.COL_INT_STUDENT_NAME not in filtered_df.columns
    ):
        return

    df_ts = filtered_df[[C.COL_INT_DATA]].copy()
    df_ts["_sid"] = _build_student_id_series(filtered_df)
    df_ts = df_ts[df_ts[C.COL_INT_DATA].notna()]
    df_ts = df_ts[df_ts["_sid"].notna() & (df_ts["_sid"] != "")]
    if df_ts.empty:
        return

    df_ts["Dia"] = pd.to_datetime(df_ts[C.COL_INT_DATA].dt.date)
    daily = (
        df_ts.groupby("Dia")
        .agg(matriculas=("_sid", "size"), alunos_unicos=("_sid", "nunique"))
        .reset_index()
        .sort_values("Dia")
    )

    by_day_ids = df_ts.groupby("Dia")["_sid"].apply(lambda s: set(s.unique())).to_dict()
    seen: set[str] = set()
    cumulative_values = []
    for d in daily["Dia"].tolist():
        seen |= by_day_ids.get(d, set())
        cumulative_values.append(len(seen))
    daily["alunos_unicos_acumulado"] = cumulative_values

    st.markdown("#### Quantidade de Alunos (Unitários)")
    series_df = daily[
        ["Dia", "alunos_unicos", "alunos_unicos_acumulado"]
    ].rename(
        columns={
            "alunos_unicos": "Alunos únicos no dia",
            "alunos_unicos_acumulado": "Alunos únicos acumulado",
        }
    )
    melt_df = series_df.melt(id_vars="Dia", var_name="Métrica", value_name="Quantidade")
    fig_students = px.line(
        melt_df,
        x="Dia",
        y="Quantidade",
        color="Métrica",
        title="Alunos Únicos: Diário vs Acumulado",
        markers=True,
    )
    st.plotly_chart(fig_students, width="stretch")
    st.divider()


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


def _render_analysis_tab(
    students_df: pd.DataFrame, faturamento_df: pd.DataFrame | None
) -> None:
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

    _render_type_pie_chart(students_df)
    _render_ticket_and_students_timeseries(filtered_df, faturamento_df)
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
    faturamento_df: pd.DataFrame | None,
    fetch_general_data: Callable[[str], Tuple[pd.DataFrame, datetime]],
    access_key: str,
    sheet_id: str = None,
) -> None:
    """
    Main render function for the Students Tab.

    Args:
        students_df (pd.DataFrame): Raw dataframe containing student data.
        faturamento_df (pd.DataFrame | None): Dataframe de faturamento para ticket médio.
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
        _render_analysis_tab(students_df, faturamento_df)
    else:
        if sheet_id:
            _render_general_tab(sheet_id, fetch_general_data)
        else:
            st.error(
                "ID da planilha não configurado. Verifique as variáveis de ambiente."
            )
