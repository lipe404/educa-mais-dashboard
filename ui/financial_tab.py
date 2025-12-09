import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
import constants as C


def render(df: pd.DataFrame, full_df: pd.DataFrame, end_date: date, selected_month: int | None):
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
    st.plotly_chart(px.line(daily, x=C.COL_INT_DATA, y=C.COL_INT_VALOR, title="Faturamento diário"), width="stretch")

    m = df.dropna(subset=[C.COL_INT_DATA]).copy()
    m["_ano"] = m[C.COL_INT_DATA].dt.year
    m["_mes"] = m[C.COL_INT_DATA].dt.month
    monthly = m.groupby(["_ano", "_mes"])[C.COL_INT_VALOR].sum().reset_index()
    pt_months = {1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"}
    monthly["Mês"] = monthly.apply(lambda r: f"{pt_months.get(int(r['_mes']), str(int(r['_mes'])))} {int(r['_ano'])}", axis=1)
    monthly = monthly.sort_values(["_ano", "_mes"]) 
    st.plotly_chart(px.bar(monthly, x="Mês", y=C.COL_INT_VALOR, title="Faturamento por mês", color_discrete_sequence=[C.COLOR_PRIMARY]), width="stretch")

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

