import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date
import constants as C


# ─── colour palette ──────────────────────────────────────────────────────────
_PINK   = "#ff2d95"
_BLUE   = "#2d9fff"
_PURPLE = "#9b27ff"
_DARK   = "#130820"
_GRAD   = ["#ff2d95", "#c724e0", "#9b27ff", "#5c33ff", "#2d9fff"]


def _kpi_card(col, label: str, value: str, sub: str = "", color: str = _PINK, icon_svg: str = ""):
    col.markdown(
        f"""
        <div style="
            background: #1e1131;
            border-left: 4px solid {color};
            border-radius: 8px;
            padding: 16px 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            position: relative;
        ">
            <div style="position:absolute; top:16px; right:16px; opacity:0.8;">
                {icon_svg}
            </div>
            <div style="font-size:0.8rem;color:#ccc;font-weight:600;letter-spacing:.05em;margin-bottom:6px;">{label}</div>
            <div style="font-size:1.6rem;font-weight:700;color:#fff;line-height:1.1;">{value}</div>
            {"<div style='font-size:0.75rem;color:#888;margin-top:6px;'>"+sub+"</div>" if sub else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_kpis(controle: pd.DataFrame, quantidade: pd.DataFrame):
    """Renders top KPI cards for bolsas data."""
    total_investido = controle[C.COL_INT_BOLSA_VALOR].sum() if not controle.empty else 0.0
    total_cotas_adquiridas = controle[C.COL_INT_BOLSA_COTAS].sum() if not controle.empty else 0
    total_cotas_disponiveis = quantidade[C.COL_INT_BOLSAQTD_QNTD].sum() if not quantidade.empty else 0
    total_compras = len(controle) if not controle.empty else 0
    total_parceiros = controle[C.COL_INT_BOLSA_PARCEIRO].nunique() if not controle.empty else 0

    ticket_medio = total_investido / total_compras if total_compras > 0 else 0.0
    cotas_por_real = total_cotas_adquiridas / total_investido if total_investido > 0 else 0.0

    icon_investido = f"<svg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='{_PINK}' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><line x1='12' y1='1' x2='12' y2='23'></line><path d='M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6'></path></svg>"
    icon_cotas_adq = f"<svg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='{_PURPLE}' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M2 9a3 3 0 0 1 0 6v2a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-2a3 3 0 0 1 0-6V7a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2z'></path><line x1='9' y1='12' x2='15' y2='12'></line></svg>"
    icon_cotas_disp = f"<svg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='{_BLUE}' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><line x1='16.5' y1='9.4' x2='7.5' y2='4.21'></line><path d='M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z'></path><polyline points='3.27 6.96 12 12.01 20.73 6.96'></polyline><line x1='12' y1='22.08' x2='12' y2='12'></line></svg>"
    icon_parceiros = f"<svg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='{_PINK}' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2'></path><circle cx='9' cy='7' r='4'></circle><path d='M23 21v-2a4 4 0 0 0-3-3.87'></path><path d='M16 3.13a4 4 0 0 1 0 7.75'></path></svg>"
    icon_ticket = f"<svg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='{_PURPLE}' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z'></path><line x1='7' y1='7' x2='7.01' y2='7'></line></svg>"

    st.markdown("### Indicadores de Bolsas")
    c1, c2, c3, c4, c5 = st.columns(5)
    _kpi_card(c1, "Total Investido", f"R$ {total_investido:,.2f}", f"{total_compras} compras", _PINK, icon_investido)
    _kpi_card(c2, "Cotas Adquiridas", f"{total_cotas_adquiridas:,}", "soma de todas compras", _PURPLE, icon_cotas_adq)
    _kpi_card(c3, "Cotas Disponíveis", f"{total_cotas_disponiveis:,}", "saldo atual", _BLUE, icon_cotas_disp)
    _kpi_card(c4, "Parceiros", f"{total_parceiros}", "com bolsas ativas", _PINK, icon_parceiros)
    _kpi_card(c5, "Ticket Médio", f"R$ {ticket_medio:,.2f}", f"{cotas_por_real:.3f} cota/R$", _PURPLE, icon_ticket)

    st.markdown("<br>", unsafe_allow_html=True)


def _render_investimento_por_parceiro(controle: pd.DataFrame):
    """Bar chart: total invested per partner."""
    if controle.empty:
        return

    by_partner = (
        controle.groupby(C.COL_INT_BOLSA_PARCEIRO)
        .agg(
            valor_total=(C.COL_INT_BOLSA_VALOR, "sum"),
            cotas_total=(C.COL_INT_BOLSA_COTAS, "sum"),
            compras=(C.COL_INT_BOLSA_VALOR, "count"),
        )
        .reset_index()
        .sort_values("valor_total", ascending=True)
    )

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=by_partner["valor_total"],
        y=by_partner[C.COL_INT_BOLSA_PARCEIRO],
        orientation="h",
        marker=dict(
            color=by_partner["valor_total"],
            colorscale=[[0, _PURPLE], [0.5, _PINK], [1, "#ff8cc8"]],
            showscale=False,
        ),
        text=[f"R$ {v:,.0f}  ({c} cotas)" for v, c in zip(by_partner["valor_total"], by_partner["cotas_total"])],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Investido: R$ %{x:,.2f}<extra></extra>",
    ))
    fig.update_layout(
        title="Investimento por Parceiro",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#ddd"),
        xaxis=dict(gridcolor="rgba(255,255,255,0.08)", title="Valor (R$)"),
        yaxis=dict(gridcolor="rgba(0,0,0,0)", title=""),
        margin=dict(l=10, r=20, t=40, b=10),
        height=max(300, len(by_partner) * 48 + 80),
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_cotas_controle(controle: pd.DataFrame, quantidade: pd.DataFrame):
    """Grouped bar: cotas adquiridas (controle) vs disponíveis (quantidade) per partner."""
    if controle.empty and quantidade.empty:
        return

    adq = (
        controle.groupby(C.COL_INT_BOLSA_PARCEIRO)[C.COL_INT_BOLSA_COTAS]
        .sum()
        .reset_index()
        .rename(columns={C.COL_INT_BOLSA_PARCEIRO: "parceiro", C.COL_INT_BOLSA_COTAS: "adquiridas"})
    ) if not controle.empty else pd.DataFrame(columns=["parceiro", "adquiridas"])

    disp = quantidade.rename(columns={
        C.COL_INT_BOLSAQTD_NOME: "parceiro",
        C.COL_INT_BOLSAQTD_QNTD: "disponiveis",
    }) if not quantidade.empty else pd.DataFrame(columns=["parceiro", "disponiveis"])

    merged = pd.merge(adq, disp, on="parceiro", how="outer").fillna(0)
    merged = merged.sort_values("adquiridas", ascending=False)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Adquiridas (histórico)",
        x=merged["parceiro"],
        y=merged["adquiridas"],
        marker_color=_PURPLE,
        opacity=0.85,
    ))
    fig.add_trace(go.Bar(
        name="Disponíveis (saldo atual)",
        x=merged["parceiro"],
        y=merged["disponiveis"],
        marker_color=_PINK,
        opacity=0.9,
    ))
    fig.update_layout(
        barmode="group",
        title="Cotas por Parceiro — Adquiridas vs Disponíveis",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#ddd"),
        xaxis=dict(gridcolor="rgba(255,255,255,0.08)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.08)", title="Cotas"),
        legend=dict(bgcolor="rgba(0,0,0,0.4)", bordercolor="rgba(255,45,149,0.33)"),
        margin=dict(l=10, r=10, t=40, b=60),
        height=400,
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_timeline(controle: pd.DataFrame):
    """Area + scatter chart: bolsa purchases over time."""
    if controle.empty or C.COL_INT_BOLSA_DATA not in controle.columns:
        return

    tmp = controle.dropna(subset=[C.COL_INT_BOLSA_DATA]).copy()
    if tmp.empty:
        return

    tmp["_mes"] = tmp[C.COL_INT_BOLSA_DATA].dt.to_period("M").astype(str)
    monthly = (
        tmp.groupby("_mes")
        .agg(
            valor=(C.COL_INT_BOLSA_VALOR, "sum"),
            cotas=(C.COL_INT_BOLSA_COTAS, "sum"),
            compras=(C.COL_INT_BOLSA_VALOR, "count"),
        )
        .reset_index()
        .sort_values("_mes")
    )

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=monthly["_mes"],
        y=monthly["valor"],
        name="Investido (R$)",
        marker=dict(
            color=monthly["valor"],
            colorscale=[[0, "#2d0050"], [0.5, _PURPLE], [1, _PINK]],
        ),
        text=[f"R$ {v:,.0f}" for v in monthly["valor"]],
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>R$ %{y:,.2f}<br>%{customdata[0]} cotas<extra></extra>",
        customdata=monthly[["cotas"]].values,
    ))
    fig.update_layout(
        title="Evolução Mensal de Investimento em Bolsas",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#ddd"),
        xaxis=dict(gridcolor="rgba(255,255,255,0.08)", title="Mês"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.08)", title="Valor (R$)"),
        margin=dict(l=10, r=10, t=40, b=10),
        height=380,
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_cotas_usadas_donut(controle: pd.DataFrame, quantidade: pd.DataFrame):
    """Donut chart: total cotas used vs available."""
    if controle.empty and quantidade.empty:
        return

    total_adq = int(controle[C.COL_INT_BOLSA_COTAS].sum()) if not controle.empty else 0
    total_disp = int(quantidade[C.COL_INT_BOLSAQTD_QNTD].sum()) if not quantidade.empty else 0
    usadas = max(0, total_adq - total_disp)

    fig = go.Figure(go.Pie(
        labels=["Cotas Utilizadas", "Cotas Disponíveis"],
        values=[usadas, total_disp],
        hole=0.62,
        marker=dict(colors=[_PINK, _BLUE], line=dict(color="#0b1437", width=2)),
        textinfo="label+percent",
        textfont=dict(size=13, color="#fff"),
        hovertemplate="<b>%{label}</b>: %{value:,} cotas (%{percent})<extra></extra>",
    ))
    fig.update_layout(
        title="Utilização de Cotas",
        annotations=[dict(
            text=f"<b>{total_adq:,}</b><br>total",
            x=0.5, y=0.5, font_size=16, font_color="#fff", showarrow=False,
        )],
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#ddd"),
        legend=dict(bgcolor="rgba(0,0,0,0.4)"),
        margin=dict(l=10, r=10, t=40, b=10),
        height=360,
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_tabela(controle: pd.DataFrame, quantidade: pd.DataFrame):
    """Data table of all bolsa records + summary table."""
    st.markdown("### Registros de Compras de Bolsas")

    if not controle.empty:
        display = controle[[
            C.COL_INT_BOLSA_PARCEIRO,
            C.COL_INT_BOLSA_VALOR,
            C.COL_INT_BOLSA_COTAS,
            C.COL_INT_BOLSA_DATA,
        ]].copy()
        display.columns = ["Parceiro", "Valor (R$)", "Cotas", "Data"]
        display["Valor (R$)"] = display["Valor (R$)"].apply(lambda x: f"R$ {x:,.2f}")
        display["Data"] = pd.to_datetime(display["Data"], errors="coerce").dt.strftime("%d/%m/%Y")
        display = display.sort_values("Data", ascending=False)
        st.dataframe(display, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum registro de bolsa encontrado.")

    st.markdown("### Saldo de Cotas por Parceiro")
    if not quantidade.empty:
        disp = quantidade[[C.COL_INT_BOLSAQTD_NOME, C.COL_INT_BOLSAQTD_QNTD]].copy()
        disp.columns = ["Parceiro", "Cotas Disponíveis"]
        disp = disp.sort_values("Cotas Disponíveis", ascending=False)
        st.dataframe(disp, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum dado de quantidade de bolsas encontrado.")


def render(
    controle: pd.DataFrame,
    quantidade: pd.DataFrame,
    start_date: date = None,
    end_date: date = None,
    selected_year: int = None,
    selected_month: int = None,
):
    """
    Main render for the Bolsas tab.

    Args:
        controle: CONTROLE DE BOLSAS dataframe — may already be date-filtered by app.py
        quantidade: QUANTIDADE BOLSAS dataframe (total available cotas per partner, no date filter)
        start_date / end_date: if provided, apply additional date filters on controle
        selected_year / selected_month: optional year/month filters
    """
    # Apply date filters to controle only if explicitly provided
    ctrl = controle.copy() if not controle.empty else pd.DataFrame()
    if (
        not ctrl.empty
        and start_date is not None
        and C.COL_INT_BOLSA_DATA in ctrl.columns
    ):
        ctrl = ctrl.dropna(subset=[C.COL_INT_BOLSA_DATA])
        ctrl = ctrl[ctrl[C.COL_INT_BOLSA_DATA].dt.date >= start_date]
        if end_date:
            ctrl = ctrl[ctrl[C.COL_INT_BOLSA_DATA].dt.date <= end_date]
        if selected_year:
            ctrl = ctrl[ctrl[C.COL_INT_BOLSA_DATA].dt.year == selected_year]
        if selected_month:
            ctrl = ctrl[ctrl[C.COL_INT_BOLSA_DATA].dt.month == selected_month]


    # ── KPIs ──────────────────────────────────────────────────────────────────
    _render_kpis(ctrl, quantidade)

    st.divider()

    # ── Row 1: investimento por parceiro + donut ───────────────────────────────
    col_bar, col_donut = st.columns([2, 1])
    with col_bar:
        _render_investimento_por_parceiro(ctrl)
    with col_donut:
        _render_cotas_usadas_donut(ctrl, quantidade)

    st.divider()

    # ── Row 2: cotas grouped bar ───────────────────────────────────────────────
    _render_cotas_controle(ctrl, quantidade)

    st.divider()

    # ── Row 3: timeline ───────────────────────────────────────────────────────
    _render_timeline(ctrl)

    st.divider()

    # ── Tables ────────────────────────────────────────────────────────────────
    _render_tabela(ctrl, quantidade)
