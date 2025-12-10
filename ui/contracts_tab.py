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

    col_a.metric("Contratos assinados", signed_count)
    col_b.metric("Contratos aguardando", waiting_count)

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

    col_c.metric("Assinados este mês", month_count)
    col_d.metric("Assinados esta semana", week_count)

    today_date = end_date if isinstance(end_date, date) else date.today()
    today_mask = signed_df[C.COL_INT_DT].dt.date == today_date
    today_count = signed_df[today_mask].drop_duplicates(subset=["_pid"]).shape[0]
    h1, h2, h3 = st.columns(3)
    h1.metric("Assinados hoje", today_count)

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
            "Acima vs semana passada"
            if diff_week > 0
            else "Falta p/ igualar semana passada"
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
        "Acima vs mês passado" if diff_month > 0 else "Falta p/ igualar mês passado",
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
    g1.plotly_chart(gauge_chart(month_count, 30, "Meta mensal 30"), width="stretch")
    g2.plotly_chart(
        gauge_chart(quarterly_count, 90, "Meta trimestral 90"), width="stretch"
    )
    g3.plotly_chart(
        gauge_chart(semiannual_count, 180, "Meta semestral 180"), width="stretch"
    )

    by_captador_base = signed_df_full.drop_duplicates(subset=["_pid"])[
        [C.COL_INT_CAPTADOR, "_pid"]
    ]
    by_captador = by_captador_base[C.COL_INT_CAPTADOR].value_counts().reset_index()
    by_captador.columns = ["Captador", "Parceiros"]
    pie_fig = px.pie(
        by_captador,
        names="Captador",
        values="Parceiros",
        title="Contratos por captador",
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
    status_df.columns = ["Status", "Quantidade"]
    bar_fig = px.bar(
        status_df[status_df["Status"].isin([C.STATUS_ASSINADO, C.STATUS_AGUARDANDO])],
        x="Status",
        y="Quantidade",
        title="Assinados vs Aguardando",
        color="Status",
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
    monthly = monthly.rename(columns={"_pid": "Contratos"})
    pt_months = {
        1: "Janeiro",
        2: "Fevereiro",
        3: "Março",
        4: "Abril",
        5: "Maio",
        6: "Junho",
        7: "Julho",
        8: "Agosto",
        9: "Setembro",
        10: "Outubro",
        11: "Novembro",
        12: "Dezembro",
    }
    monthly["Mês"] = monthly.apply(
        lambda r: f"{pt_months.get(int(r['_mes']), str(int(r['_mes'])))} {int(r['_ano'])}",
        axis=1,
    )
    monthly = monthly.sort_values(["_ano", "_mes"])
    fig_month = px.bar(
        monthly,
        x="Mês",
        y="Contratos",
        title="Contratos assinados por mês",
        color_discrete_sequence=[C.COLOR_PRIMARY],
    )
    st.plotly_chart(fig_month, width="stretch")
