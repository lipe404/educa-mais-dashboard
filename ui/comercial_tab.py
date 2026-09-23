import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date
import datetime
import constants as C


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_sum(df: pd.DataFrame, col: str) -> float:
    if df.empty or col not in df.columns:
        return 0.0
    return float(df[col].sum())


def _filter_by_date(df: pd.DataFrame, col: str, ref_date: date) -> pd.DataFrame:
    return df[df[col].dt.date == ref_date]


def _filter_from_date(df: pd.DataFrame, col: str, from_date: date) -> pd.DataFrame:
    return df[df[col].dt.date >= from_date]


# ---------------------------------------------------------------------------
# KPI section
# ---------------------------------------------------------------------------

def _render_comercial_kpis(df: pd.DataFrame) -> None:
    today = date.today()
    start_of_week = today - datetime.timedelta(days=today.weekday())
    start_of_month = today.replace(day=1)

    if df.empty or C.COL_INT_DATA not in df.columns:
        total = hoje = semana = mes = 0.0
        count = 0
    else:
        tmp = df.dropna(subset=[C.COL_INT_DATA])
        total = _safe_sum(tmp, C.COL_INT_VALOR)
        hoje = _safe_sum(_filter_by_date(tmp, C.COL_INT_DATA, today), C.COL_INT_VALOR)
        semana = _safe_sum(_filter_from_date(tmp, C.COL_INT_DATA, start_of_week), C.COL_INT_VALOR)
        mes = _safe_sum(_filter_from_date(tmp, C.COL_INT_DATA, start_of_month), C.COL_INT_VALOR)
        count = len(tmp)

    ticket = total / count if count > 0 else 0.0

    st.markdown(
        "<p style='color:#ff8c00;font-weight:700;font-size:1rem;margin-bottom:4px;'>"
        "🏪 Comercial Interno — Vendas Diretas (sem comissão de parceiro)</p>",
        unsafe_allow_html=True,
    )

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Total (período)", f"R$ {total:,.2f}")
    k2.metric("Hoje", f"R$ {hoje:,.2f}")
    k3.metric("Esta Semana", f"R$ {semana:,.2f}")
    k4.metric("Este Mês", f"R$ {mes:,.2f}")
    k5.metric("Ticket Médio", f"R$ {ticket:,.2f}")
    st.caption(f"📋 {count} transações no período")


# ---------------------------------------------------------------------------
# Daily chart
# ---------------------------------------------------------------------------

def _render_daily_chart(df: pd.DataFrame) -> None:
    if df.empty or C.COL_INT_DATA not in df.columns:
        st.info("Sem dados de faturamento Comercial Interno para o período selecionado.")
        return

    tmp = df.dropna(subset=[C.COL_INT_DATA]).copy()
    daily = (
        tmp.groupby(tmp[C.COL_INT_DATA].dt.date)[C.COL_INT_VALOR]
        .sum()
        .reset_index()
    )
    daily.columns = ["Data", "Valor"]

    fig = px.bar(
        daily,
        x="Data",
        y="Valor",
        title="Faturamento Diário — Comercial Interno",
        color_discrete_sequence=["#ff8c00"],
    )
    fig.update_yaxes(tickprefix="R$ ", tickformat=",.2f")
    fig.update_layout(hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# Monthly chart
# ---------------------------------------------------------------------------

def _render_monthly_chart(df: pd.DataFrame) -> None:
    if df.empty or C.COL_INT_DATA not in df.columns:
        return

    tmp = df.dropna(subset=[C.COL_INT_DATA]).copy()
    tmp["_ano"] = tmp[C.COL_INT_DATA].dt.year
    tmp["_mes"] = tmp[C.COL_INT_DATA].dt.month
    monthly = tmp.groupby(["_ano", "_mes"])[C.COL_INT_VALOR].sum().reset_index()
    monthly["Mês"] = monthly.apply(
        lambda r: f"{C.MONTH_NAMES.get(int(r['_mes']), str(int(r['_mes'])))} {int(r['_ano'])}",
        axis=1,
    )

    show_ranking = st.toggle(
        "Ordenar por Maior Faturamento (Ranking)", value=False, key="comercial_ranking_toggle"
    )

    if show_ranking:
        monthly = monthly.sort_values(C.COL_INT_VALOR, ascending=False)
        title = "🏆 Ranking de Faturamento por Mês — Comercial Interno"
    else:
        monthly = monthly.sort_values(["_ano", "_mes"])
        title = "Faturamento por Mês — Comercial Interno"

    fig = px.bar(
        monthly,
        x="Mês",
        y=C.COL_INT_VALOR,
        title=title,
        color_discrete_sequence=["#ff8c00"],
    )
    fig.update_yaxes(tickprefix="R$ ", tickformat=",.2f")
    st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# Month-vs-month comparison
# ---------------------------------------------------------------------------

def _render_month_comparison(
    full_df: pd.DataFrame, focus_year: int, focus_month: int
) -> None:
    prev_year = focus_year if focus_month > 1 else focus_year - 1
    prev_month = focus_month - 1 if focus_month > 1 else 12

    cur_mask = (
        (full_df[C.COL_INT_DATA].dt.year == focus_year)
        & (full_df[C.COL_INT_DATA].dt.month == focus_month)
    )
    prev_mask = (
        (full_df[C.COL_INT_DATA].dt.year == prev_year)
        & (full_df[C.COL_INT_DATA].dt.month == prev_month)
    )

    cur_total = float(full_df.loc[cur_mask, C.COL_INT_VALOR].sum())
    prev_total = float(full_df.loc[prev_mask, C.COL_INT_VALOR].sum())
    diff = cur_total - prev_total
    pct = (cur_total / prev_total * 100.0) if prev_total > 0 else None

    cur_name = f"{C.MONTH_NAMES.get(focus_month, focus_month)}/{focus_year}"
    prev_name = f"{C.MONTH_NAMES.get(prev_month, prev_month)}/{prev_year}"

    c1, c2, c3 = st.columns(3)
    c1.metric(f"Mês Atual ({cur_name})", f"R$ {cur_total:,.2f}")
    c2.metric(f"Mês Anterior ({prev_name})", f"R$ {prev_total:,.2f}")
    c3.metric(
        "Acima do mês anterior" if diff >= 0 else "Falta para igualar mês anterior",
        f"R$ {abs(diff):,.2f}",
        delta=f"{pct:.1f}%" if pct is not None else None,
    )

    # Build daily chart for comparison
    df_curr = full_df[cur_mask].copy()
    df_prev = full_df[prev_mask].copy()

    daily_curr = (
        df_curr.groupby(df_curr[C.COL_INT_DATA].dt.day)[C.COL_INT_VALOR]
        .sum()
        .reset_index()
    )
    daily_curr.columns = ["Dia", "Valor"]

    daily_prev = (
        df_prev.groupby(df_prev[C.COL_INT_DATA].dt.day)[C.COL_INT_VALOR]
        .sum()
        .reset_index()
    )
    daily_prev.columns = ["Dia", "Valor"]

    all_days = pd.DataFrame({"Dia": range(1, 32)})
    merged = all_days.merge(daily_curr, on="Dia", how="left").rename(columns={"Valor": "Atual"})
    merged = merged.merge(daily_prev, on="Dia", how="left").rename(columns={"Valor": "Anterior"})
    merged = merged.fillna(0)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=merged["Dia"], y=merged["Anterior"],
        name=f"Mês Anterior ({prev_name})",
        marker_color="rgba(255,140,0,0.35)", opacity=0.8,
    ))
    fig.add_trace(go.Bar(
        x=merged["Dia"], y=merged["Atual"],
        name=f"Mês Atual ({cur_name})",
        marker_color="#ff8c00",
    ))
    fig.update_layout(
        title=f"Comparativo Diário: {cur_name} vs {prev_name}",
        xaxis_title="Dia",
        yaxis_title="Valor (R$)",
        barmode="group",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(range=[0.5, 31.5], dtick=1)
    st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# Transaction table
# ---------------------------------------------------------------------------

def _render_transaction_table(df: pd.DataFrame) -> None:
    if df.empty:
        st.info("Nenhuma transação encontrada.")
        return

    cols_display = []
    col_labels = {}

    if C.COL_INT_DATA in df.columns:
        cols_display.append(C.COL_INT_DATA)
        col_labels[C.COL_INT_DATA] = "Data"
    if C.COL_INT_PARTNER in df.columns:
        cols_display.append(C.COL_INT_PARTNER)
        col_labels[C.COL_INT_PARTNER] = "Vendedor / Parceiro"
    if C.COL_INT_STUDENT_NAME in df.columns:
        cols_display.append(C.COL_INT_STUDENT_NAME)
        col_labels[C.COL_INT_STUDENT_NAME] = "Nome do Aluno"
    if C.COL_INT_COURSE in df.columns:
        cols_display.append(C.COL_INT_COURSE)
        col_labels[C.COL_INT_COURSE] = "Curso"
    if C.COL_INT_VALOR in df.columns:
        cols_display.append(C.COL_INT_VALOR)
        col_labels[C.COL_INT_VALOR] = "Valor (R$)"

    display = df[cols_display].copy()
    display = display.rename(columns=col_labels)

    if "Data" in display.columns:
        display["Data"] = pd.to_datetime(display["Data"]).dt.strftime("%d/%m/%Y")

    if "Valor (R$)" in display.columns:
        display = display.sort_values("Valor (R$)", ascending=False)
        display["Valor (R$)"] = display["Valor (R$)"].apply(lambda x: f"R$ {x:,.2f}")

    st.dataframe(display, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# Main render
# ---------------------------------------------------------------------------

def render(
    df: pd.DataFrame,
    full_df: pd.DataFrame,
    end_date: date,
    selected_month: int | None,
) -> None:
    """
    Renders the Comercial Interno tab.

    Parameters
    ----------
    df        : faturamento filtered for the selected period (COMERCIAL TEC only)
    full_df   : full faturamento history (COMERCIAL TEC only, no date filter)
    end_date  : the end date of the current filter (used to determine focus month)
    selected_month : explicitly selected month (or None)
    """
    st.markdown("## 🏪 Comercial Interno")
    st.markdown(
        "Vendas realizadas diretamente pela equipe interna, sem intermediação de parceiros. "
        "Este faturamento **não entra nos cálculos de comissão de parceiros**."
    )
    st.divider()

    now = date.today()
    focus_year = end_date.year if isinstance(end_date, date) else now.year
    focus_month = (
        selected_month
        if selected_month is not None
        else end_date.month if isinstance(end_date, date) else now.month
    )

    # --- 1. KPIs ---
    _render_comercial_kpis(df)
    st.divider()

    # --- 2. Tabs within the page ---
    tab_daily, tab_monthly, tab_compare, tab_table = st.tabs([
        "📅 Faturamento Diário",
        "📊 Por Mês",
        "🔀 Comparativo",
        "📋 Transações",
    ])

    with tab_daily:
        _render_daily_chart(df)

    with tab_monthly:
        _render_monthly_chart(df)

    with tab_compare:
        if full_df.empty or C.COL_INT_DATA not in full_df.columns:
            st.info("Sem dados históricos para comparação.")
        else:
            _render_month_comparison(full_df, focus_year, focus_month)

    with tab_table:
        st.markdown("### Transações do Período")
        _render_transaction_table(df)
