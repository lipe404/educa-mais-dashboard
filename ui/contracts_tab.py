import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta
import constants as C
from ui.components import gauge_chart


def _enrich_df(df: pd.DataFrame) -> pd.DataFrame:
    """Adds helper columns like _pid for unique identification."""
    df = df.copy()
    df["_pid"] = df[C.COL_INT_PARTNER].astype(str).str.strip()
    df["_pid"] = df["_pid"].where(
        df["_pid"] != "",
        df[C.COL_INT_CEP].astype(str).str.strip(),
    )
    df["_pid"] = df["_pid"].where(
        df["_pid"] != "",
        df[C.COL_INT_CITY].astype(str).str.strip()
        + "|"
        + df[C.COL_INT_STATE].astype(str).str.strip(),
    )
    return df


def _calculate_kpis(
    df: pd.DataFrame, end_date: date, selected_month: int | None
) -> dict:
    """
    Calculates key performance indicators (KPIs) for contracts.

    Args:
        df (pd.DataFrame): The input dataframe containing contract data.
        end_date (date): The end date for the analysis period.
        selected_month (int | None): The selected month for filtering, or None for current month.

    Returns:
        dict: A dictionary containing calculated KPIs such as signed count, waiting count,
              monthly/weekly counts, and reference dates.
    """
    status_counts = df[C.COL_INT_STATUS].value_counts()
    
    # Full dataset logic for "Assinado"
    signed_df_full = df[df[C.COL_INT_STATUS] == C.STATUS_ASSINADO].copy()
    signed_df_full = _enrich_df(signed_df_full)
    signed_count = signed_df_full.drop_duplicates(subset=["_pid"]).shape[0]
    waiting_count = int(status_counts.get(C.STATUS_AGUARDANDO, 0))

    now = date.today()
    focus_year = end_date.year if isinstance(end_date, date) else now.year
    focus_month = selected_month if selected_month is not None else now.month

    # Filtered dataset for time-based metrics
    signed_df = signed_df_full  # Already filtered by status=Assinado and enriched
    
    month_mask = (signed_df[C.COL_INT_DT].dt.year == focus_year) & (
        signed_df[C.COL_INT_DT].dt.month == focus_month
    )
    month_count = signed_df[month_mask].drop_duplicates(subset=["_pid"]).shape[0]

    week_end_date = end_date if isinstance(end_date, date) else date.today()
    week_start_date = week_end_date - timedelta(days=week_end_date.weekday())
    week_mask = (signed_df[C.COL_INT_DT].dt.date >= week_start_date) & (
        signed_df[C.COL_INT_DT].dt.date <= (week_start_date + timedelta(days=6))
    )
    week_count = signed_df[week_mask].drop_duplicates(subset=["_pid"]).shape[0]

    return {
        "signed_count": signed_count,
        "waiting_count": waiting_count,
        "month_count": month_count,
        "week_count": week_count,
        "focus_year": focus_year,
        "focus_month": focus_month,
        "signed_df": signed_df,
        "week_start_date": week_start_date,
    }


def _render_kpi_metrics(kpis: dict):
    """
    Renders the top-level KPI metrics (Signed, Waiting, Month, Week).

    Args:
        kpis (dict): A dictionary containing calculated KPIs from `_calculate_kpis`.
    """
    col_a, col_b, col_c, col_d = st.columns([1, 1, 1, 1])
    col_a.metric(C.UI_LABEL_CONTRACTS_SIGNED, kpis["signed_count"])
    col_b.metric(C.UI_LABEL_CONTRACTS_WAITING, kpis["waiting_count"])
    col_c.metric(C.UI_LABEL_SIGNED_MONTH, kpis["month_count"])
    col_d.metric(C.UI_LABEL_SIGNED_WEEK, kpis["week_count"])


def _render_detailed_metrics(kpis: dict, end_date: date):
    """
    Renders detailed comparison metrics (Today vs Last Week vs Last Month).

    Args:
        kpis (dict): A dictionary containing calculated KPIs from `_calculate_kpis`.
        end_date (date): The reference date for "today" calculation.
    """
    signed_df = kpis["signed_df"]
    week_count = kpis["week_count"]
    month_count = kpis["month_count"]
    focus_year = kpis["focus_year"]
    focus_month = kpis["focus_month"]
    week_start_date = kpis["week_start_date"]

    today_date = end_date if isinstance(end_date, date) else date.today()
    today_mask = signed_df[C.COL_INT_DT].dt.date == today_date
    today_count = signed_df[today_mask].drop_duplicates(subset=["_pid"]).shape[0]
    
    h1, h2, h3 = st.columns(3)
    h1.metric(C.UI_LABEL_SIGNED_TODAY, today_count)

    last_week_start = week_start_date - timedelta(days=7)
    last_week_mask = (signed_df[C.COL_INT_DT].dt.date >= last_week_start) & (
        signed_df[C.COL_INT_DT].dt.date <= (last_week_start + timedelta(days=6))
    )
    last_week_count = (
        signed_df[last_week_mask].drop_duplicates(subset=["_pid"]).shape[0]
    )
    diff_week = week_count - last_week_count
    progress_pct_week = (
        (week_count / last_week_count * 100.0) if last_week_count > 0 else None
    )
    h2.metric(
        (C.UI_LABEL_VS_LAST_WEEK_UP if diff_week > 0 else C.UI_LABEL_VS_LAST_WEEK_DOWN),
        abs(diff_week),
        delta=(f"{progress_pct_week:.1f}%" if progress_pct_week is not None else None),
    )

    prev_year = focus_year if focus_month > 1 else focus_year - 1
    prev_month = focus_month - 1 if focus_month > 1 else 12
    last_month_mask = (signed_df[C.COL_INT_DT].dt.year == prev_year) & (
        signed_df[C.COL_INT_DT].dt.month == prev_month
    )
    last_month_count = (
        signed_df[last_month_mask].drop_duplicates(subset=["_pid"]).shape[0]
    )
    diff_month = month_count - last_month_count
    progress_pct_month = (
        (month_count / last_month_count * 100.0) if last_month_count > 0 else None
    )
    h3.metric(
        (
            C.UI_LABEL_VS_LAST_MONTH_UP
            if diff_month > 0
            else C.UI_LABEL_VS_LAST_MONTH_DOWN
        ),
        abs(diff_month),
        delta=(
            f"{progress_pct_month:.1f}%" if progress_pct_month is not None else None
        ),
    )


def _render_gauges(kpis: dict):
    """
    Renders gauge charts for Monthly, Quarterly, and Semiannual goals.

    Args:
        kpis (dict): A dictionary containing calculated KPIs from `_calculate_kpis`.
    """
    signed_df = kpis["signed_df"]
    focus_year = kpis["focus_year"]
    focus_month = kpis["focus_month"]
    month_count = kpis["month_count"]

    q_start = ((focus_month - 1) // 3) * 3 + 1
    quarterly_mask = (
        (signed_df[C.COL_INT_DT].dt.year == focus_year)
        & (signed_df[C.COL_INT_DT].dt.month >= q_start)
        & (signed_df[C.COL_INT_DT].dt.month <= q_start + 2)
    )
    quarterly_count = (
        signed_df[quarterly_mask].drop_duplicates(subset=["_pid"]).shape[0]
    )

    sem_start = 1 if focus_month <= 6 else 7
    semestral_mask = (
        (signed_df[C.COL_INT_DT].dt.year == focus_year)
        & (signed_df[C.COL_INT_DT].dt.month >= sem_start)
        & (signed_df[C.COL_INT_DT].dt.month <= sem_start + 5)
    )
    semiannual_count = (
        signed_df[semestral_mask].drop_duplicates(subset=["_pid"]).shape[0]
    )

    g1, g2, g3 = st.columns([1, 1, 1])
    g1.plotly_chart(
        gauge_chart(month_count, 30, C.UI_LABEL_GOAL_MONTHLY), width="stretch"
    )
    g2.plotly_chart(
        gauge_chart(quarterly_count, 90, C.UI_LABEL_GOAL_QUARTERLY), width="stretch"
    )
    g3.plotly_chart(
        gauge_chart(semiannual_count, 180, C.UI_LABEL_GOAL_SEMIANNUAL), width="stretch"
    )


def _render_captador_pie(df: pd.DataFrame):
    """
    Renders a pie chart showing contract distribution by 'Captador'.

    Args:
        df (pd.DataFrame): The input dataframe containing contract data.
    """
    signed_df_full = df[df[C.COL_INT_STATUS] == C.STATUS_ASSINADO].copy()
    signed_df_full = _enrich_df(signed_df_full)
    
    by_captador_base = signed_df_full.drop_duplicates(subset=["_pid"])[
        [C.COL_INT_CAPTADOR, "_pid"]
    ]
    by_captador = by_captador_base[C.COL_INT_CAPTADOR].value_counts().reset_index()
    by_captador.columns = [C.UI_LABEL_CAPTADOR, C.UI_LABEL_PARTNERS]
    pie_fig = px.pie(
        by_captador,
        names=C.UI_LABEL_CAPTADOR,
        values=C.UI_LABEL_PARTNERS,
        title=C.UI_LABEL_CONTRACTS_BY_CAPTADOR,
        color_discrete_sequence=px.colors.sequential.Pinkyl,
    )
    st.plotly_chart(pie_fig, width="stretch")


def _render_status_bar(df: pd.DataFrame):
    """
    Renders a bar chart comparing Signed vs Waiting contracts.

    Args:
        df (pd.DataFrame): The input dataframe containing contract data.
    """
    df_status = df.copy()
    df_status = _enrich_df(df_status)
    rank_map = {C.STATUS_ASSINADO: 2, C.STATUS_AGUARDANDO: 1, C.STATUS_CANCELADO: 0}
    df_status["_rank"] = df_status[C.COL_INT_STATUS].map(rank_map).fillna(-1)
    df_partner = df_status.sort_values("_rank", ascending=False).drop_duplicates(
        subset=["_pid"]
    )
    status_counts_dedup = df_partner[C.COL_INT_STATUS].value_counts()
    status_df = status_counts_dedup.reindex(
        [C.STATUS_ASSINADO, C.STATUS_AGUARDANDO, C.STATUS_CANCELADO], fill_value=0
    ).reset_index()
    status_df.columns = [C.UI_LABEL_STATUS, C.UI_LABEL_QUANTITY]
    bar_fig = px.bar(
        status_df[
            status_df[C.UI_LABEL_STATUS].isin([C.STATUS_ASSINADO, C.STATUS_AGUARDANDO])
        ],
        x=C.UI_LABEL_STATUS,
        y=C.UI_LABEL_QUANTITY,
        title=C.UI_LABEL_SIGNED_VS_WAITING,
        color=C.UI_LABEL_STATUS,
        color_discrete_map={
            C.STATUS_ASSINADO: C.COLOR_PRIMARY,
            C.STATUS_AGUARDANDO: C.COLOR_SECONDARY,
        },
    )
    st.plotly_chart(bar_fig, width="stretch")


def _render_monthly_evolution(df: pd.DataFrame):
    """
    Renders a bar chart showing the monthly evolution of signed contracts.

    Args:
        df (pd.DataFrame): The input dataframe containing contract data.

    Returns:
        tuple: A tuple containing the plotly event object and the filtered dataframe of signed contracts.
    """
    signed_only = df[df[C.COL_INT_STATUS] == C.STATUS_ASSINADO].copy()
    signed_only = signed_only.dropna(subset=[C.COL_INT_DT])
    signed_only = _enrich_df(signed_only)
    
    signed_only["_ano"] = signed_only[C.COL_INT_DT].dt.year
    signed_only["_mes"] = signed_only[C.COL_INT_DT].dt.month
    monthly = signed_only.groupby(["_ano", "_mes"])[["_pid"]].nunique().reset_index()
    monthly = monthly.rename(columns={"_pid": C.UI_LABEL_CONTRACTS})

    if not monthly.empty:
        monthly[C.UI_LABEL_MONTH] = monthly.apply(
            lambda r: f"{C.MONTH_NAMES.get(int(r['_mes']), str(int(r['_mes'])))} {int(r['_ano'])}",
            axis=1,
        )
    else:
        monthly[C.UI_LABEL_MONTH] = pd.Series(dtype="string")

    monthly = monthly.sort_values(["_ano", "_mes"])
    fig_month = px.bar(
        monthly,
        x=C.UI_LABEL_MONTH,
        y=C.UI_LABEL_CONTRACTS,
        title=C.UI_LABEL_SIGNED_BY_MONTH,
        color_discrete_sequence=[C.COLOR_PRIMARY],
        custom_data=["_ano", "_mes"],
    )

    # Meta Visual
    fig_month.add_hline(
        y=C.GOAL_MONTHLY_CONTRACTS,
        line_dash="dash",
        line_color="green",
        annotation_text="Meta",
        annotation_position="top right",
    )

    # Detalhamento Diário (Interativo)
    event = st.plotly_chart(
        fig_month,
        width="stretch",
        on_select="rerun",
        selection_mode="points",
        key="monthly_chart_click",
    )
    return event, signed_only


def _render_weekday_hour_heatmap(signed_only: pd.DataFrame) -> None:
    if signed_only.empty or C.COL_INT_DT not in signed_only.columns:
        return

    base = signed_only.dropna(subset=[C.COL_INT_DT]).copy()
    if base.empty:
        return

    if "_pid" not in base.columns:
        base = _enrich_df(base)

    base["_dow"] = base[C.COL_INT_DT].dt.dayofweek
    base["_hour"] = base[C.COL_INT_DT].dt.hour

    g = (
        base.groupby(["_dow", "_hour"])["_pid"]
        .nunique()
        .reset_index(name=C.UI_LABEL_CONTRACTS)
    )
    if g.empty:
        return

    pivot = (
        g.pivot(index="_dow", columns="_hour", values=C.UI_LABEL_CONTRACTS)
        .reindex(index=list(range(7)), columns=list(range(24)))
        .fillna(0)
        .astype(int)
    )

    day_labels = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
    pivot.index = day_labels

    st.markdown("#### Heatmap: Assinaturas por Dia da Semana × Hora")
    fig = px.imshow(
        pivot,
        aspect="auto",
        text_auto=True,
        color_continuous_scale="Blues",
        labels={"x": "Hora", "y": "Dia da semana", "color": C.UI_LABEL_CONTRACTS},
        title="Distribuição de Assinaturas (7×24)",
    )
    st.plotly_chart(fig, width="stretch")


def _render_captador_bump_chart(signed_only: pd.DataFrame) -> None:
    if signed_only.empty:
        return
    if C.COL_INT_CAPTADOR not in signed_only.columns or C.COL_INT_DT not in signed_only.columns:
        return

    base = signed_only.dropna(subset=[C.COL_INT_DT]).copy()
    if base.empty:
        return

    if "_pid" not in base.columns:
        base = _enrich_df(base)

    base = base[base["_pid"].notna() & (base["_pid"] != "")]
    base = base[base[C.COL_INT_CAPTADOR].notna() & (base[C.COL_INT_CAPTADOR] != "")]
    if base.empty:
        return

    base["_ano"] = base[C.COL_INT_DT].dt.year
    base["_mes"] = base[C.COL_INT_DT].dt.month

    monthly = (
        base.drop_duplicates(subset=["_pid", "_ano", "_mes"])
        .groupby(["_ano", "_mes", C.COL_INT_CAPTADOR])["_pid"]
        .nunique()
        .reset_index(name=C.UI_LABEL_CONTRACTS)
    )
    if monthly.empty:
        return

    monthly["rank"] = monthly.groupby(["_ano", "_mes"])[C.UI_LABEL_CONTRACTS].rank(
        method="dense", ascending=False
    )
    monthly["rank"] = monthly["rank"].astype(int)

    monthly[C.UI_LABEL_MONTH] = monthly.apply(
        lambda r: f"{C.MONTH_NAMES.get(int(r['_mes']), str(int(r['_mes'])))} {int(r['_ano'])}",
        axis=1,
    )
    month_order = (
        monthly[["_ano", "_mes", C.UI_LABEL_MONTH]]
        .drop_duplicates()
        .sort_values(["_ano", "_mes"])[C.UI_LABEL_MONTH]
        .tolist()
    )

    st.markdown("#### Bump Chart: Ranking de Captadores por Mês")
    fig = px.line(
        monthly,
        x=C.UI_LABEL_MONTH,
        y="rank",
        color=C.COL_INT_CAPTADOR,
        markers=True,
        title="Ranking Mensal de Captadores (quanto menor, melhor)",
        category_orders={C.UI_LABEL_MONTH: month_order},
    )
    fig.update_yaxes(autorange="reversed", dtick=1, title="Rank")
    fig.update_xaxes(title="")
    st.plotly_chart(fig, width="stretch")


def _render_contracts_treemap(signed_only: pd.DataFrame) -> None:
    if signed_only.empty:
        return
    required = [C.COL_INT_DT, C.COL_INT_STATE, C.COL_INT_CAPTADOR]
    if any(c not in signed_only.columns for c in required):
        return

    base = signed_only.dropna(subset=[C.COL_INT_DT]).copy()
    if base.empty:
        return

    if "_pid" not in base.columns:
        base = _enrich_df(base)

    if C.COL_INT_REGION not in base.columns and C.COL_INT_STATE in base.columns:
        base[C.COL_INT_REGION] = (
            base[C.COL_INT_STATE].map(C.ESTADO_REGIAO).fillna(C.DEFAULT_REGION_OTHER)
        )

    base = base[base["_pid"].notna() & (base["_pid"] != "")]
    base = base[
        base[C.COL_INT_STATE].notna()
        & (base[C.COL_INT_STATE] != "")
        & base[C.COL_INT_CAPTADOR].notna()
        & (base[C.COL_INT_CAPTADOR] != "")
        & base[C.COL_INT_REGION].notna()
        & (base[C.COL_INT_REGION] != "")
    ]
    if base.empty:
        return

    dedup = base.drop_duplicates(subset=["_pid"])[
        [C.COL_INT_REGION, C.COL_INT_STATE, C.COL_INT_CAPTADOR, "_pid"]
    ].copy()

    g = (
        dedup.groupby([C.COL_INT_REGION, C.COL_INT_STATE, C.COL_INT_CAPTADOR])["_pid"]
        .nunique()
        .reset_index(name=C.UI_LABEL_CONTRACTS)
    )
    if g.empty:
        return

    st.markdown("#### Treemap: Região → Estado → Captador")
    fig = px.treemap(
        g,
        path=[C.COL_INT_REGION, C.COL_INT_STATE, C.COL_INT_CAPTADOR],
        values=C.UI_LABEL_CONTRACTS,
        color=C.UI_LABEL_CONTRACTS,
        color_continuous_scale="Blues",
        title="Distribuição de Contratos (Assinados) por Região/Estado/Captador",
    )
    fig.update_traces(textinfo="label+value")
    st.plotly_chart(fig, width="stretch")


def _render_daily_drilldown(event, signed_only: pd.DataFrame, kpis: dict, selected_month: int | None):
    """
    Renders a daily drilldown chart based on user selection or default month.

    Args:
        event: The plotly selection event from the monthly evolution chart.
        signed_only (pd.DataFrame): The dataframe containing only signed contracts.
        kpis (dict): A dictionary containing calculated KPIs from `_calculate_kpis`.
        selected_month (int | None): The selected month for filtering, or None.
    """
    focus_year = kpis["focus_year"]
    focus_month = kpis["focus_month"]
    
    target_year = None
    target_month = None

    # Prioridade: 1. Filtro da Sidebar, 2. Clique no Gráfico
    if selected_month:
        target_year = focus_year
        target_month = focus_month
    elif event and event.selection and event.selection["points"]:
        point = event.selection["points"][0]

        # 1. Try Custom Data (Robust)
        if "customdata" in point:
            cd = point["customdata"]
            if isinstance(cd, list) and len(cd) >= 2:
                target_year = int(cd[0])
                target_month = int(cd[1])
            elif isinstance(cd, dict):
                target_year = int(cd.get("_ano", 0))
                target_month = int(cd.get("_mes", 0))

        # 2. Fallback: Parse from X-Axis (e.g., "Outubro 2025")
        if (target_year == 0 or target_month == 0) and "x" in point:
            x_val = point["x"]
            try:
                # Expected format: "MonthName Year"
                parts = x_val.split(" ")
                if len(parts) == 2:
                    m_name = parts[0]
                    y_str = parts[1]
                    target_year = int(y_str)

                    # Reverse lookup for month
                    for k, v in C.MONTH_NAMES.items():
                        if v == m_name:
                            target_month = k
                            break
            except Exception:
                pass

    if target_year and target_month:
        daily_mask = (signed_only["_ano"] == target_year) & (
            signed_only["_mes"] == target_month
        )
        daily_df = signed_only[daily_mask].copy()

        # Agrupar por dia
        daily_counts = (
            daily_df.groupby(daily_df[C.COL_INT_DT].dt.day)[C.COL_INT_PARTNER]
            .nunique()
            .reset_index()
        )
        daily_counts.columns = ["Dia", C.UI_LABEL_CONTRACTS]

        month_name = C.MONTH_NAMES.get(target_month, str(target_month))

        fig_daily = px.bar(
            daily_counts,
            x="Dia",
            y=C.UI_LABEL_CONTRACTS,
            title=f"{C.UI_LABEL_DAILY_SALES} - {month_name}/{target_year}",
            color_discrete_sequence=[C.COLOR_SECONDARY],
            text=C.UI_LABEL_CONTRACTS,
        )
        fig_daily.update_traces(textposition="outside")
        st.plotly_chart(fig_daily, width="stretch")


def render(df: pd.DataFrame, end_date: date, selected_month: int | None):
    """
    Main render function for the Contracts Tab.

    Orchestrates the rendering of all sub-components: KPIs, Charts, and Detailed Tables.

    Args:
        df (pd.DataFrame): The input dataframe containing contract data.
        end_date (date): The end date for the analysis period.
        selected_month (int | None): The selected month for filtering, or None.
    """
    # 1. Metrics Top Row
    kpis = _calculate_kpis(df, end_date, selected_month)
    _render_kpi_metrics(kpis)
    
    # 2. Detailed Metrics (Comparison)
    _render_detailed_metrics(kpis, end_date)
    
    st.divider()

    # 3. Gauges
    _render_gauges(kpis)

    st.divider()

    # 4. Pie Chart
    _render_captador_pie(df)
    
    st.divider()

    # 5. Status Bar Chart
    _render_status_bar(df)

    # 6. Monthly Evolution & Daily Drilldown
    event, signed_only = _render_monthly_evolution(df)
    _render_weekday_hour_heatmap(signed_only)
    _render_captador_bump_chart(signed_only)
    _render_contracts_treemap(signed_only)
    
    st.divider()
    
    _render_daily_drilldown(event, signed_only, kpis, selected_month)
