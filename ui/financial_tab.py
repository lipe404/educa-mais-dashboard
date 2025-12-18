import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
import datetime
import constants as C


def render(
    df: pd.DataFrame, full_df: pd.DataFrame, end_date: date, selected_month: int | None
):
    total = df[C.COL_INT_VALOR].sum()
    parceiros = (df[C.COL_INT_VALOR] * df[C.COL_INT_COMISSAO]).sum()
    equipe = C.COMMISSION_RATE_TEAM * (total - parceiros)
    liquido = total - parceiros - equipe

    # Novos KPIs
    today = date.today()
    fat_hoje = df[df[C.COL_INT_DATA].dt.date == today][C.COL_INT_VALOR].sum()
    start_of_week = today - datetime.timedelta(days=today.weekday())
    end_of_week = start_of_week + datetime.timedelta(days=6)
    fat_semana = df[(df[C.COL_INT_DATA].dt.date >= start_of_week) & (df[C.COL_INT_DATA].dt.date <= end_of_week)][C.COL_INT_VALOR].sum()
    start_of_month = today.replace(day=1)
    fat_mes = df[df[C.COL_INT_DATA].dt.date >= start_of_month][C.COL_INT_VALOR].sum()

    new_k1, new_k2, new_k3 = st.columns(3)
    new_k1.metric(C.UI_LABEL_REVENUE_TODAY, f"R$ {fat_hoje:,.2f}")
    new_k2.metric(C.UI_LABEL_REVENUE_WEEK, f"R$ {fat_semana:,.2f}")
    new_k3.metric(C.UI_LABEL_REVENUE_MONTH, f"R$ {fat_mes:,.2f}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(C.UI_LABEL_TOTAL_REVENUE, f"R$ {total:,.2f}")
    c2.metric(C.UI_LABEL_PARTNER_COMMISSION, f"R$ {parceiros:,.2f}")
    c3.metric(f"{C.UI_LABEL_TEAM_COMMISSION_BASE} ({int(C.COMMISSION_RATE_TEAM*100)}%)", f"R$ {equipe:,.2f}")
    c4.metric(C.UI_LABEL_NET_REVENUE, f"R$ {liquido:,.2f}")

    daily = df.groupby(df[C.COL_INT_DATA].dt.date)[C.COL_INT_VALOR].sum().reset_index()
    daily.columns = [C.COL_INT_DATA, C.COL_INT_VALOR]
    st.plotly_chart(
        px.line(daily, x=C.COL_INT_DATA, y=C.COL_INT_VALOR, title=C.UI_LABEL_DAILY_REVENUE),
        width="stretch",
    )

    m = df.dropna(subset=[C.COL_INT_DATA]).copy()
    m["_ano"] = m[C.COL_INT_DATA].dt.year
    m["_mes"] = m[C.COL_INT_DATA].dt.month
    monthly = m.groupby(["_ano", "_mes"])[C.COL_INT_VALOR].sum().reset_index()
    if not monthly.empty:
        monthly[C.UI_LABEL_MONTH] = monthly.apply(
            lambda r: f"{C.MONTH_NAMES.get(int(r['_mes']), str(int(r['_mes'])))} {int(r['_ano'])}",
            axis=1,
        )
    else:
        monthly[C.UI_LABEL_MONTH] = []

    monthly = monthly.sort_values(["_ano", "_mes"])
    st.plotly_chart(
        px.bar(
            monthly,
            x=C.UI_LABEL_MONTH,
            y=C.COL_INT_VALOR,
            title=C.UI_LABEL_MONTHLY_REVENUE,
            color_discrete_sequence=[C.COLOR_PRIMARY],
        ),
        width="stretch",
    )

    now = date.today()
    focus_year = end_date.year if isinstance(end_date, date) else now.year
    focus_month = selected_month if selected_month is not None else now.month
    prev_year = focus_year if focus_month > 1 else focus_year - 1
    prev_month = focus_month - 1 if focus_month > 1 else 12
    cur_mask = (full_df[C.COL_INT_DATA].dt.year == focus_year) & (
        full_df[C.COL_INT_DATA].dt.month == focus_month
    )
    prev_mask = (full_df[C.COL_INT_DATA].dt.year == prev_year) & (
        full_df[C.COL_INT_DATA].dt.month == prev_month
    )
    cur_total_month = float(full_df.loc[cur_mask, C.COL_INT_VALOR].sum())
    prev_total_month = float(full_df.loc[prev_mask, C.COL_INT_VALOR].sum())
    diff = cur_total_month - prev_total_month
    progress_pct = (
        (cur_total_month / prev_total_month * 100.0) if prev_total_month > 0 else None
    )
    k1, k2, k3 = st.columns(3)
    k1.metric(C.UI_LABEL_REVENUE_CURRENT_MONTH, f"R$ {cur_total_month:,.2f}")
    k2.metric(C.UI_LABEL_GOAL_LAST_MONTH, f"R$ {prev_total_month:,.2f}")
    k3.metric(
        C.UI_LABEL_VS_LAST_MONTH_REV_UP if diff > 0 else C.UI_LABEL_VS_LAST_MONTH_REV_DOWN,
        f"R$ {abs(diff):,.2f}",
        delta=(f"{progress_pct:.1f}%" if progress_pct is not None else None),
    )

    st.markdown(C.UI_LABEL_SIMULATOR_TITLE)
    sim_add = st.number_input(
        C.UI_LABEL_SIMULATOR_INPUT, min_value=0.0, step=100.0, value=0.0
    )
    avg_comissao = (parceiros / total) if total > 0 else 0.0
    sim_total = total + sim_add
    sim_parceiros = parceiros + sim_add * avg_comissao
    sim_equipe = C.COMMISSION_RATE_TEAM * (sim_total - sim_parceiros)
    sim_liquido = sim_total - sim_parceiros - sim_equipe
    s1, s2, s3, s4 = st.columns(4)
    s1.metric(C.UI_LABEL_SIMULATOR_TOTAL, f"R$ {sim_total:,.2f}")
    s2.metric(C.UI_LABEL_SIMULATOR_PARTNER, f"R$ {sim_parceiros:,.2f}")
    s3.metric(f"{C.UI_LABEL_SIMULATOR_TEAM} ({int(C.COMMISSION_RATE_TEAM*100)}%) (simulado)", f"R$ {sim_equipe:,.2f}")
    s4.metric(C.UI_LABEL_SIMULATOR_NET, f"R$ {sim_liquido:,.2f}")
    cur_total_month_sim = cur_total_month + sim_add
    diff_sim = cur_total_month_sim - prev_total_month
    progress_pct_sim = (
        (cur_total_month_sim / prev_total_month * 100.0)
        if prev_total_month > 0
        else None
    )
    st.metric(
        (
            C.UI_LABEL_SIMULATOR_VS_LAST_UP
            if diff_sim > 0
            else C.UI_LABEL_SIMULATOR_VS_LAST_DOWN
        ),
        f"R$ {abs(diff_sim):,.2f}",
        delta=(f"{progress_pct_sim:.1f}%" if progress_pct_sim is not None else None),
    )
