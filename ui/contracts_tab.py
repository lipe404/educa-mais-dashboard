import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta
import constants as C
from ui.components import gauge_chart


def render(df: pd.DataFrame, end_date: date, selected_month: int | None):
    col_a, col_b, col_c, col_d = st.columns([1, 1, 1, 1])

    status_counts = df[C.COL_INT_STATUS].value_counts()
    signed_df_full = df[df[C.COL_INT_STATUS] == C.STATUS_ASSINADO].copy()
    signed_df_full["_pid"] = signed_df_full[C.COL_INT_PARTNER].astype(str).str.strip()
    signed_df_full["_pid"] = signed_df_full["_pid"].where(
        signed_df_full["_pid"] != "",
        signed_df_full[C.COL_INT_CEP].astype(str).str.strip(),
    )
    signed_df_full["_pid"] = signed_df_full["_pid"].where(
        signed_df_full["_pid"] != "",
        signed_df_full[C.COL_INT_CITY].astype(str).str.strip()
        + "|"
        + signed_df_full[C.COL_INT_STATE].astype(str).str.strip(),
    )
    signed_count = signed_df_full.drop_duplicates(subset=["_pid"]).shape[0]
    waiting_count = int(status_counts.get(C.STATUS_AGUARDANDO, 0))

    col_a.metric(C.UI_LABEL_CONTRACTS_SIGNED, signed_count)
    col_b.metric(C.UI_LABEL_CONTRACTS_WAITING, waiting_count)

    now = date.today()
    focus_year = end_date.year if isinstance(end_date, date) else now.year
    focus_month = selected_month if selected_month is not None else now.month

    signed_df = df[df[C.COL_INT_STATUS] == C.STATUS_ASSINADO].copy()
    signed_df["_pid"] = signed_df[C.COL_INT_PARTNER].astype(str).str.strip()
    signed_df["_pid"] = signed_df["_pid"].where(
        signed_df["_pid"] != "",
        signed_df[C.COL_INT_CEP].astype(str).str.strip(),
    )
    signed_df["_pid"] = signed_df["_pid"].where(
        signed_df["_pid"] != "",
        signed_df[C.COL_INT_CITY].astype(str).str.strip()
        + "|"
        + signed_df[C.COL_INT_STATE].astype(str).str.strip(),
    )

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

    col_c.metric(C.UI_LABEL_SIGNED_MONTH, month_count)
    col_d.metric(C.UI_LABEL_SIGNED_WEEK, week_count)

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
        (
            C.UI_LABEL_VS_LAST_WEEK_UP
            if diff_week > 0
            else C.UI_LABEL_VS_LAST_WEEK_DOWN
        ),
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
        C.UI_LABEL_VS_LAST_MONTH_UP if diff_month > 0 else C.UI_LABEL_VS_LAST_MONTH_DOWN,
        abs(diff_month),
        delta=(
            f"{progress_pct_month:.1f}%" if progress_pct_month is not None else None
        ),
    )

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
    g1.plotly_chart(gauge_chart(month_count, 30, C.UI_LABEL_GOAL_MONTHLY), width="stretch")
    g2.plotly_chart(
        gauge_chart(quarterly_count, 90, C.UI_LABEL_GOAL_QUARTERLY), width="stretch"
    )
    g3.plotly_chart(
        gauge_chart(semiannual_count, 180, C.UI_LABEL_GOAL_SEMIANNUAL), width="stretch"
    )

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

    df_status = df.copy()
    df_status["_pid"] = df_status[C.COL_INT_PARTNER].astype(str).str.strip()
    df_status["_pid"] = df_status["_pid"].where(
        df_status["_pid"] != "",
        df_status[C.COL_INT_CEP].astype(str).str.strip(),
    )
    df_status["_pid"] = df_status["_pid"].where(
        df_status["_pid"] != "",
        df_status[C.COL_INT_CITY].astype(str).str.strip()
        + "|"
        + df_status[C.COL_INT_STATE].astype(str).str.strip(),
    )
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
        status_df[status_df[C.UI_LABEL_STATUS].isin([C.STATUS_ASSINADO, C.STATUS_AGUARDANDO])],
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

    signed_only = df[df[C.COL_INT_STATUS] == C.STATUS_ASSINADO].copy()
    signed_only = signed_only.dropna(subset=[C.COL_INT_DT])
    signed_only["_pid"] = signed_only[C.COL_INT_PARTNER].astype(str).str.strip()
    signed_only["_pid"] = signed_only["_pid"].where(
        signed_only["_pid"] != "",
        signed_only[C.COL_INT_CEP].astype(str).str.strip(),
    )
    signed_only["_pid"] = signed_only["_pid"].where(
        signed_only["_pid"] != "",
        signed_only[C.COL_INT_CITY].astype(str).str.strip()
        + "|"
        + signed_only[C.COL_INT_STATE].astype(str).str.strip(),
    )
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
        monthly[C.UI_LABEL_MONTH] = pd.Series(dtype='string')
        
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
        annotation_position="top right"
    )

    # Detalhamento Diário (Interativo)
    event = st.plotly_chart(
        fig_month, 
        width="stretch", 
        on_select="rerun", 
        selection_mode="points", 
        key="monthly_chart_click"
    )

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
                parts = x_val.split(' ')
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
        daily_mask = (signed_only["_ano"] == target_year) & (signed_only["_mes"] == target_month)
        daily_df = signed_only[daily_mask].copy()
        
        # Agrupar por dia
        daily_counts = daily_df.groupby(daily_df[C.COL_INT_DT].dt.day)[C.COL_INT_PARTNER].nunique().reset_index()
        daily_counts.columns = ["Dia", C.UI_LABEL_CONTRACTS]
        
        month_name = C.MONTH_NAMES.get(target_month, str(target_month))
        
        fig_daily = px.bar(
            daily_counts,
            x="Dia",
            y=C.UI_LABEL_CONTRACTS,
            title=f"{C.UI_LABEL_DAILY_SALES} - {month_name}/{target_year}",
            color_discrete_sequence=[C.COLOR_SECONDARY],
            text=C.UI_LABEL_CONTRACTS
        )
        fig_daily.update_traces(textposition='outside')
        st.plotly_chart(fig_daily, width="stretch")
