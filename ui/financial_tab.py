import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Tuple
from datetime import date
import datetime
import constants as C


def _calculate_kpis(df: pd.DataFrame) -> dict:
    total = df[C.COL_INT_VALOR].sum()
    parceiros = (df[C.COL_INT_VALOR] * df[C.COL_INT_COMISSAO]).sum()
    equipe = C.COMMISSION_RATE_TEAM * (total - parceiros)
    liquido = total - parceiros - equipe

    # Novos KPIs
    today = date.today()
    fat_hoje = df[df[C.COL_INT_DATA].dt.date == today][C.COL_INT_VALOR].sum()
    start_of_week = today - datetime.timedelta(days=today.weekday())
    end_of_week = start_of_week + datetime.timedelta(days=6)
    fat_semana = df[
        (df[C.COL_INT_DATA].dt.date >= start_of_week)
        & (df[C.COL_INT_DATA].dt.date <= end_of_week)
    ][C.COL_INT_VALOR].sum()
    start_of_month = today.replace(day=1)
    fat_mes = df[df[C.COL_INT_DATA].dt.date >= start_of_month][C.COL_INT_VALOR].sum()

    return {
        "total": total,
        "parceiros": parceiros,
        "equipe": equipe,
        "liquido": liquido,
        "fat_hoje": fat_hoje,
        "fat_semana": fat_semana,
        "fat_mes": fat_mes,
    }


def _render_kpis(kpis: dict):
    new_k1, new_k2, new_k3 = st.columns(3)
    new_k1.metric(C.UI_LABEL_REVENUE_TODAY, f"R$ {kpis['fat_hoje']:,.2f}")
    new_k2.metric(C.UI_LABEL_REVENUE_WEEK, f"R$ {kpis['fat_semana']:,.2f}")
    new_k3.metric(C.UI_LABEL_REVENUE_MONTH, f"R$ {kpis['fat_mes']:,.2f}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(C.UI_LABEL_TOTAL_REVENUE, f"R$ {kpis['total']:,.2f}")
    c2.metric(C.UI_LABEL_PARTNER_COMMISSION, f"R$ {kpis['parceiros']:,.2f}")
    c3.metric(
        f"{C.UI_LABEL_TEAM_COMMISSION_BASE} ({int(C.COMMISSION_RATE_TEAM*100)}%)",
        f"R$ {kpis['equipe']:,.2f}",
    )
    c4.metric(C.UI_LABEL_NET_REVENUE, f"R$ {kpis['liquido']:,.2f}")


def _render_sankey_chart(kpis: dict):
    total = float(kpis.get("total", 0.0) or 0.0)
    parceiros = float(kpis.get("parceiros", 0.0) or 0.0)
    equipe_total = float(kpis.get("equipe", 0.0) or 0.0)
    liquido = float(kpis.get("liquido", 0.0) or 0.0)

    base_equipe = max(0.0, total - parceiros)

    equipe_fixa = max(0.0, min(equipe_total, base_equipe))
    equipe_variavel = max(0.0, base_equipe - equipe_fixa - liquido)
    liquido_sankey = max(0.0, base_equipe - equipe_fixa - equipe_variavel)

    labels = [
        "Faturamento Bruto",
        "Comissão Parceiros",
        "Base Equipe",
        "Comissão Equipe (Fixa)",
        "Comissão Equipe (Variável)",
        "Resultado Líquido",
    ]
    idx = {label: i for i, label in enumerate(labels)}

    sources = [
        idx["Faturamento Bruto"],
        idx["Faturamento Bruto"],
        idx["Base Equipe"],
        idx["Base Equipe"],
        idx["Base Equipe"],
    ]
    targets = [
        idx["Comissão Parceiros"],
        idx["Base Equipe"],
        idx["Comissão Equipe (Fixa)"],
        idx["Comissão Equipe (Variável)"],
        idx["Resultado Líquido"],
    ]
    values = [parceiros, base_equipe, equipe_fixa, equipe_variavel, liquido_sankey]

    link_colors = [
        "rgba(239,85,59,0.55)",
        "rgba(45,159,255,0.35)",
        "rgba(239,85,59,0.55)",
        "rgba(239,85,59,0.35)",
        "rgba(0,204,150,0.55)",
    ]
    node_colors = [
        "rgba(45,159,255,0.9)",
        "rgba(239,85,59,0.9)",
        "rgba(45,159,255,0.6)",
        "rgba(239,85,59,0.8)",
        "rgba(239,85,59,0.55)",
        "rgba(0,204,150,0.9)",
    ]

    fig = go.Figure(
        data=[
            go.Sankey(
                arrangement="snap",
                node=dict(
                    pad=18,
                    thickness=18,
                    line=dict(color="rgba(0,0,0,0.15)", width=1),
                    label=labels,
                    color=node_colors,
                ),
                link=dict(
                    source=sources,
                    target=targets,
                    value=values,
                    color=link_colors,
                    hovertemplate="R$ %{value:,.2f}<extra></extra>",
                ),
            )
        ]
    )

    fig.update_layout(
        title="Fluxo de Receita (Sankey)",
        font=dict(size=12),
        margin=dict(l=20, r=20, t=50, b=20),
    )

    st.plotly_chart(fig, use_container_width=True)


def _render_daily_comparison_chart(
    full_df: pd.DataFrame, df: pd.DataFrame, focus_year: int, focus_month: int, prev_year: int, prev_month: int
):
    show_comparison = st.toggle("Comparar com Mês Anterior (Mês vs Mês)", value=False)

    if show_comparison:
        show_cumulative = st.toggle("Comparativo de Cumulativo", value=False)

        # 1. Prepare Data
        curr_mask = (full_df[C.COL_INT_DATA].dt.year == focus_year) & (
            full_df[C.COL_INT_DATA].dt.month == focus_month
        )
        df_curr = full_df[curr_mask].copy()

        prev_mask = (full_df[C.COL_INT_DATA].dt.year == prev_year) & (
            full_df[C.COL_INT_DATA].dt.month == prev_month
        )
        df_prev = full_df[prev_mask].copy()

        # Calculate Total Previous Month for Milestone
        total_prev_month = df_prev[C.COL_INT_VALOR].sum()

        # Group by Day
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

        # Create full range 1-31 for merging
        all_days = pd.DataFrame({"Dia": range(1, 32)})

        # Merge Daily Data
        merged = all_days.merge(daily_curr, on="Dia", how="left").rename(
            columns={"Valor": "Atual"}
        )
        merged = merged.merge(daily_prev, on="Dia", how="left").rename(
            columns={"Valor": "Anterior"}
        )

        # Fill NaN with 0 only for calculations, but keep track of valid days for plotting
        merged_calc = merged.fillna(0)

        # Milestone: Check when we surpassed previous month total
        milestone_day = None
        current_cumulative_series = merged_calc["Atual"].cumsum()

        # Find first day where cumulative current > total_prev_month
        surpassed_mask = current_cumulative_series > total_prev_month
        if surpassed_mask.any():
            idx = surpassed_mask.idxmax()
            milestone_day = merged_calc.iloc[idx]["Dia"]

        if show_cumulative:
            _render_cumulative_chart(
                merged, merged_calc, focus_month, focus_year, prev_month, prev_year, milestone_day
            )
        else:
            _render_daily_bar_chart(
                merged_calc, focus_month, focus_year, prev_month, prev_year, milestone_day
            )

        st.divider()

    else:
        daily = (
            df.groupby(df[C.COL_INT_DATA].dt.date)[C.COL_INT_VALOR].sum().reset_index()
        )
        daily.columns = [C.COL_INT_DATA, C.COL_INT_VALOR]
        st.plotly_chart(
            px.line(
                daily,
                x=C.COL_INT_DATA,
                y=C.COL_INT_VALOR,
                title=C.UI_LABEL_DAILY_REVENUE,
            ),
            width="stretch",
        )
        st.divider()


def _render_cumulative_chart(
    merged, merged_calc, focus_month, focus_year, prev_month, prev_year, milestone_day
):
    # --- CUMULATIVE: LINE CHART ---
    chart_title = f"Comparativo Cumulativo: {focus_month:02d}/{focus_year} vs {prev_month:02d}/{prev_year}"

    # Prepare Cumulative Data
    # For Current month: We want cumulative sum up to the last valid day, then NaN
    # Identify last valid index for current month
    last_valid_idx = merged["Atual"].last_valid_index()

    cum_atual = merged_calc["Atual"].cumsum()
    cum_anterior = merged_calc["Anterior"].cumsum()

    # Mask future days for Current Month
    if last_valid_idx is not None:
        cum_atual[last_valid_idx + 1 :] = None
    else:
        # If no data at all for current month
        cum_atual[:] = None

    fig = go.Figure()

    # Previous Month Line
    fig.add_trace(
        go.Scatter(
            x=merged["Dia"],
            y=cum_anterior,
            mode="lines",
            name=f"Mês Anterior ({prev_month:02d}/{prev_year})",
            line=dict(color="gray", dash="dot", width=2),
            hovertemplate="Dia %{x}: R$ %{y:,.2f}<extra></extra>",
        )
    )

    # Current Month Line
    fig.add_trace(
        go.Scatter(
            x=merged["Dia"],
            y=cum_atual,
            mode="lines+markers",
            name=f"Mês Atual ({focus_month:02d}/{focus_year})",
            line=dict(color=C.COLOR_PRIMARY, width=3),
            marker=dict(size=6),
            hovertemplate="Dia %{x}: R$ %{y:,.2f}<extra></extra>",
        )
    )

    # Milestone Annotation (Meta Batida)
    if milestone_day:
        fig.add_vline(
            x=milestone_day,
            line_width=2,
            line_dash="dash",
            line_color="green",
            annotation_text=f"Meta Batida (Dia {int(milestone_day)})",
            annotation_position="top left",
        )
        st.success(
            f"🚀 Faturamento do mês anterior superado no dia **{int(milestone_day)}**!"
        )

    # Equivalence Indicator: "Where were we last month with today's revenue?"
    # Get latest cumulative value for current month
    if last_valid_idx is not None:
        current_val = cum_atual[last_valid_idx]
        current_day = merged.iloc[last_valid_idx]["Dia"]

        # Find day in previous month where cumulative >= current_val
        # We search in cum_anterior
        equiv_mask = cum_anterior >= current_val
        if equiv_mask.any():
            equiv_idx = equiv_mask.idxmax()
            equiv_day = merged.iloc[equiv_idx]["Dia"]

            # Add Horizontal Line from Current Point to Previous Curve
            fig.add_shape(
                type="line",
                x0=current_day,
                y0=current_val,
                x1=equiv_day,
                y1=current_val,
                line=dict(color="orange", width=1, dash="dot"),
            )

            # Add Annotation
            fig.add_annotation(
                x=equiv_day,
                y=current_val,
                text=f"Mesmo fat. no dia {int(equiv_day)}",
                showarrow=True,
                arrowhead=1,
                ax=0,
                ay=-20,
                bgcolor="rgba(255, 165, 0, 0.2)",
            )

    fig.update_layout(
        title=chart_title,
        xaxis_title="Dia",
        yaxis_title="Valor Acumulado (R$)",
        hovermode="x unified",
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
        ),
    )
    fig.update_xaxes(range=[0.5, 31.5], dtick=1)
    st.plotly_chart(fig, width="stretch")


def _render_daily_bar_chart(
    merged_plot, focus_month, focus_year, prev_month, prev_year, milestone_day
):
    # --- DAILY: BAR CHART ---
    chart_title = f"Comparativo Diário: {focus_month:02d}/{focus_year} vs {prev_month:02d}/{prev_year}"

    fig = go.Figure()

    # Previous Month (Bar - Gray/Muted)
    fig.add_trace(
        go.Bar(
            x=merged_plot["Dia"],
            y=merged_plot["Anterior"],
            name=f"Mês Anterior ({prev_month:02d}/{prev_year})",
            marker_color="lightgray",
            opacity=0.7,
        )
    )

    # Current Month (Bar - Colored)
    fig.add_trace(
        go.Bar(
            x=merged_plot["Dia"],
            y=merged_plot["Atual"],
            name=f"Mês Atual ({focus_month:02d}/{focus_year})",
            marker_color=C.COLOR_PRIMARY,
            textposition="auto",
        )
    )

    # Add "Winner" indicators
    winning_days = merged_plot[merged_plot["Atual"] > merged_plot["Anterior"]]
    if not winning_days.empty:
        fig.add_trace(
            go.Scatter(
                x=winning_days["Dia"],
                y=winning_days["Atual"],
                mode="markers",
                marker=dict(
                    symbol="star",
                    size=10,
                    color="gold",
                    line=dict(width=1, color="darkorange"),
                ),
                name="Superou Mês Anterior",
                hoverinfo="skip",
            )
        )

    # Add Milestone Annotation
    if milestone_day:
        fig.add_vline(
            x=milestone_day,
            line_width=2,
            line_dash="dash",
            line_color="green",
            annotation_text=f"Meta Batida (Dia {int(milestone_day)})",
            annotation_position="top right",
        )
        st.success(
            f"🚀 Faturamento do mês anterior superado no dia **{int(milestone_day)}**!"
        )

    fig.update_layout(
        title=chart_title,
        xaxis_title="Dia",
        yaxis_title="Valor (R$)",
        barmode="group",
        hovermode="x unified",
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
        ),
    )
    fig.update_xaxes(range=[0.5, 31.5], dtick=1)
    st.plotly_chart(fig, width="stretch")


def _render_monthly_chart(df: pd.DataFrame):
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
        monthly[C.UI_LABEL_MONTH] = pd.Series(dtype="string")

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
    st.divider()


def _render_month_vs_month_kpis(
    full_df: pd.DataFrame, focus_year: int, focus_month: int, prev_year: int, prev_month: int
) -> Tuple[float, float]:
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
        (
            C.UI_LABEL_VS_LAST_MONTH_REV_UP
            if diff > 0
            else C.UI_LABEL_VS_LAST_MONTH_REV_DOWN
        ),
        f"R$ {abs(diff):,.2f}",
        delta=(f"{progress_pct:.1f}%" if progress_pct is not None else None),
    )
    st.divider()
    return cur_total_month, prev_total_month


def _render_simulator(
    kpis: dict, cur_total_month: float, prev_total_month: float
):
    total = kpis["total"]
    parceiros = kpis["parceiros"]
    
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
    s3.metric(
        f"{C.UI_LABEL_SIMULATOR_TEAM} ({int(C.COMMISSION_RATE_TEAM*100)}%) (simulado)",
        f"R$ {sim_equipe:,.2f}",
    )
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


def render(
    df: pd.DataFrame, full_df: pd.DataFrame, end_date: date, selected_month: int | None
):
    # 1. Calculate and Render Main KPIs
    kpis = _calculate_kpis(df)
    _render_kpis(kpis)

    with st.expander("Ver Detalhes do Resultado (Sankey)", expanded=False):
        _render_sankey_chart(kpis)

    st.divider()

    # 2. Daily Revenue Comparison
    now = date.today()
    focus_year = end_date.year if isinstance(end_date, date) else now.year
    focus_month = (
        selected_month
        if selected_month is not None
        else end_date.month if isinstance(end_date, date) else now.month
    )
    prev_year = focus_year if focus_month > 1 else focus_year - 1
    prev_month = focus_month - 1 if focus_month > 1 else 12

    _render_daily_comparison_chart(
        full_df, df, focus_year, focus_month, prev_year, prev_month
    )

    # 3. Monthly Revenue Chart
    _render_monthly_chart(df)

    # 4. Month vs Month KPIs
    cur_total_month, prev_total_month = _render_month_vs_month_kpis(
        full_df, focus_year, focus_month, prev_year, prev_month
    )

    # 5. Simulator
    _render_simulator(kpis, cur_total_month, prev_total_month)
