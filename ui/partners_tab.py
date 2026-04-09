import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import constants as C
from typing import Optional


def _check_authentication(access_key: str) -> bool:
    """
    Handles access control for the Partners tab by verifying the provided access key.

    Args:
        access_key (str): The expected correct access key.

    Returns:
        bool: True if the user enters the correct key, False otherwise.
    """
    key = st.text_input(
        C.UI_LABEL_ACCESS_KEY, type="password", key="partners_access_key"
    )
    if key != access_key:
        st.warning(C.UI_LABEL_ENTER_KEY_MSG)
        return False
    return True


def _aggregate_partner_sales(fat_df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates sales and revenue by partner.

    Args:
        fat_df (pd.DataFrame): DataFrame containing financial/sales data.

    Returns:
        pd.DataFrame: A DataFrame with columns 'Parceiro', 'total_vendas', and 'total_faturamento',
                      aggregated by partner. Returns an empty DataFrame if input is empty.
    """
    if fat_df.empty:
        return pd.DataFrame()

    partner_sales = (
        fat_df.groupby(C.COL_INT_PARTNER)
        .agg(
            total_vendas=(C.COL_INT_VALOR, "count"),
            total_faturamento=(C.COL_INT_VALOR, "sum"),
        )
        .reset_index()
    )

    # Filter out empty partners
    partner_sales = partner_sales[partner_sales[C.COL_INT_PARTNER] != ""]
    return partner_sales


def _render_sales_chart(partner_sales: pd.DataFrame) -> None:
    """
    Renders a bar chart showing the top 10 partners by number of sales.

    Args:
        partner_sales (pd.DataFrame): Aggregated DataFrame containing partner sales data.
    """
    # Sort by total sales (descending)
    partner_sales_sorted = partner_sales.sort_values("total_vendas", ascending=False)
    top_sales = partner_sales_sorted.head(10)

    fig_sales = px.bar(
        top_sales,
        x=C.COL_INT_PARTNER,
        y="total_vendas",
        title=C.UI_LABEL_TOP_10_SALES,
        labels={
            C.COL_INT_PARTNER: C.UI_LABEL_PARTNER,
            "total_vendas": C.UI_LABEL_NUM_SALES,
        },
        color="total_vendas",
        color_continuous_scale=px.colors.sequential.Pinkyl,
        text_auto=True,
    )
    fig_sales.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_sales, width="stretch")


def _render_revenue_chart(partner_sales: pd.DataFrame) -> None:
    """
    Renders a bar chart showing the top 10 partners by total revenue.

    Args:
        partner_sales (pd.DataFrame): Aggregated DataFrame containing partner sales data.
    """
    # Sort by total revenue (descending)
    partner_sales_rev = partner_sales.sort_values("total_faturamento", ascending=False)
    top_revenue = partner_sales_rev.head(10)

    fig_revenue = px.bar(
        top_revenue,
        x=C.COL_INT_PARTNER,
        y="total_faturamento",
        title=C.UI_LABEL_TOP_10_REVENUE,
        labels={
            C.COL_INT_PARTNER: C.UI_LABEL_PARTNER,
            "total_faturamento": C.UI_LABEL_TOTAL_REVENUE_CURRENCY,
        },
        color="total_faturamento",
        color_continuous_scale=px.colors.sequential.Blues,
        text_auto=".2f",
    )
    fig_revenue.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_revenue, width="stretch")


def _render_partner_pareto(partner_sales: pd.DataFrame) -> None:
    base = partner_sales[[C.COL_INT_PARTNER, "total_faturamento"]].copy()
    base[C.COL_INT_PARTNER] = base[C.COL_INT_PARTNER].astype(str).str.strip()
    base = base[base[C.COL_INT_PARTNER] != ""]
    base = base.sort_values("total_faturamento", ascending=False)
    if base.empty:
        return

    total = float(base["total_faturamento"].sum())
    if total <= 0:
        return

    n_partners = int(len(base))
    base["pct_acum_full"] = (base["total_faturamento"] / total).cumsum() * 100.0
    k_80 = int((base["pct_acum_full"] >= 80.0).values.argmax() + 1) if (base["pct_acum_full"] >= 80.0).any() else n_partners

    top_n = 20
    top = base.head(top_n).copy()
    others_sum = float(base.iloc[top_n:]["total_faturamento"].sum()) if n_partners > top_n else 0.0

    plot_rows = []
    for i, (_, r) in enumerate(top.iterrows(), start=1):
        plot_rows.append(
            {
                "rank_num": int(i),
                "rank_label": str(i),
                "partner": str(r[C.COL_INT_PARTNER]),
                "total_faturamento": float(r["total_faturamento"]),
            }
        )
    if others_sum > 0:
        plot_rows.append(
            {
                "rank_num": int(top_n + 1),
                "rank_label": "Outros",
                "partner": f"Outros ({n_partners - top_n} parceiros)",
                "total_faturamento": float(others_sum),
            }
        )

    plot_df = pd.DataFrame(plot_rows)
    plot_df["pct_acum"] = (plot_df["total_faturamento"] / total).cumsum() * 100.0

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=plot_df["rank_num"],
            y=plot_df["total_faturamento"],
            name="Faturamento",
            marker_color=C.COLOR_PRIMARY,
            customdata=plot_df["partner"],
            hovertemplate="Parceiro: %{customdata}<br>R$ %{y:,.2f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=plot_df["rank_num"],
            y=plot_df["pct_acum"],
            name="% acumulado",
            yaxis="y2",
            mode="lines+markers",
            line=dict(color="rgba(255,255,255,0.75)", width=2),
            marker=dict(size=6),
            hovertemplate="% acumulado: %{y:.1f}%<extra></extra>",
        )
    )

    if (plot_df["pct_acum"] >= 80.0).any():
        cut_pos = int((plot_df["pct_acum"] >= 80.0).values.argmax())
        cut_x = float(plot_df.iloc[cut_pos]["rank_num"])
        fig.add_vline(
            x=cut_x,
            line_width=2,
            line_dash="dot",
            line_color="rgba(0,204,150,0.9)",
            annotation_text="corte 80%",
            annotation_position="top left",
        )
    fig.update_layout(
        title="Curva de Pareto: parceiros por faturamento",
        xaxis=dict(title="Ranking (por faturamento)", tickangle=0),
        yaxis=dict(title="Faturamento (R$)"),
        yaxis2=dict(
            title="% acumulado",
            overlaying="y",
            side="right",
            range=[0, 100],
            ticksuffix="%",
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=10, r=10, t=60, b=10),
        height=520,
    )
    fig.update_xaxes(
        tickmode="array",
        tickvals=plot_df["rank_num"].tolist(),
        ticktext=plot_df["rank_label"].tolist(),
    )
    fig.update_yaxes(tickprefix="R$ ", tickformat=",.0f")
    st.plotly_chart(fig, width="stretch")

    st.caption(
        f"~80% do faturamento vem dos top {k_80} parceiros ({(k_80 / n_partners * 100.0):.1f}% dos parceiros)."
    )


def _render_partner_ticket_volume_scatter(partner_sales: pd.DataFrame) -> None:
    base = partner_sales[[C.COL_INT_PARTNER, "total_vendas", "total_faturamento"]].copy()
    base[C.COL_INT_PARTNER] = base[C.COL_INT_PARTNER].astype(str).str.strip()
    base["total_vendas"] = pd.to_numeric(base["total_vendas"], errors="coerce")
    base["total_faturamento"] = pd.to_numeric(base["total_faturamento"], errors="coerce")
    base = base.dropna(subset=["total_vendas", "total_faturamento"])
    base = base[(base[C.COL_INT_PARTNER] != "") & (base["total_vendas"] > 0) & (base["total_faturamento"] > 0)]
    if base.empty:
        return

    base["ticket_medio"] = base["total_faturamento"] / base["total_vendas"]
    med_vendas = float(base["total_vendas"].median())
    med_ticket = float(base["ticket_medio"].median())

    base["_quad"] = np.select(
        [
            (base["total_vendas"] >= med_vendas) & (base["ticket_medio"] >= med_ticket),
            (base["total_vendas"] >= med_vendas) & (base["ticket_medio"] < med_ticket),
            (base["total_vendas"] < med_vendas) & (base["ticket_medio"] >= med_ticket),
        ],
        ["Alto volume / Alto ticket", "Alto volume / Baixo ticket", "Baixo volume / Alto ticket"],
        default="Baixo volume / Baixo ticket",
    )

    top_labels = (
        base.sort_values("total_faturamento", ascending=False)
        .head(15)[C.COL_INT_PARTNER]
        .tolist()
    )
    base["_text"] = base[C.COL_INT_PARTNER].where(base[C.COL_INT_PARTNER].isin(top_labels), "")

    st.markdown("### Scatter: ticket médio × volume de vendas por parceiro")
    fig = px.scatter(
        base,
        x="total_vendas",
        y="ticket_medio",
        size="total_faturamento",
        color="_quad",
        text="_text",
        size_max=55,
        labels={
            "total_vendas": "Nº de vendas",
            "ticket_medio": "Ticket médio (R$)",
            "total_faturamento": "Faturamento total (R$)",
            "_quad": "Quadrante",
        },
        title="Segmentação de parceiros por volume e ticket",
        hover_data={
            C.COL_INT_PARTNER: True,
            "total_vendas": True,
            "ticket_medio": ":.2f",
            "total_faturamento": ":.2f",
            "_quad": True,
            "_text": False,
        },
    )
    fig.update_traces(textposition="top center")
    fig.add_vline(x=med_vendas, line_dash="dot", line_color="rgba(255,255,255,0.35)")
    fig.add_hline(y=med_ticket, line_dash="dot", line_color="rgba(255,255,255,0.35)")
    fig.update_yaxes(tickprefix="R$ ", tickformat=",.2f")
    fig.update_layout(margin=dict(l=10, r=10, t=60, b=10), height=560)
    st.plotly_chart(fig, width="stretch")


def _render_summary_metrics(partner_sales: pd.DataFrame) -> None:
    """
    Renders summary metrics for partners, including total count and top performers.

    Args:
        partner_sales (pd.DataFrame): Aggregated DataFrame containing partner sales data.
    """
    top_sales = partner_sales.sort_values("total_vendas", ascending=False).head(1)
    top_revenue = partner_sales.sort_values("total_faturamento", ascending=False).head(1)

    col1, col2, col3 = st.columns(3)
    col1.metric(C.UI_LABEL_TOTAL_PARTNERS, len(partner_sales))
    
    if not top_sales.empty:
        col2.metric(C.UI_LABEL_PARTNER_MOST_SALES, top_sales.iloc[0][C.COL_INT_PARTNER])
    
    if not top_revenue.empty:
        col3.metric(C.UI_LABEL_PARTNER_MOST_REVENUE, top_revenue.iloc[0][C.COL_INT_PARTNER])


def _render_detailed_table(partner_sales: pd.DataFrame) -> None:
    """Renders the detailed table of partner sales."""
    st.markdown(C.UI_LABEL_PARTNERS_DETAILS_TITLE)
    
    # Sort by sales for the table view
    table_df = partner_sales.sort_values("total_vendas", ascending=False).rename(
        columns={
            C.COL_INT_PARTNER: C.UI_LABEL_PARTNER,
            "total_vendas": C.UI_LABEL_NUM_SALES,
            "total_faturamento": C.UI_LABEL_TOTAL_REVENUE_CURRENCY,
        }
    ).reset_index(drop=True)
    
    table_df[C.UI_LABEL_TOTAL_REVENUE_CURRENCY] = table_df[
        C.UI_LABEL_TOTAL_REVENUE_CURRENCY
    ].apply(lambda x: f"R$ {x:,.2f}")
    st.dataframe(table_df)


def _render_partner_location_filter(dados_df: pd.DataFrame) -> None:
    """
    Renders a section to filter and view partners by location (City/State).
    Filters for partners with 'ASSINADO' status in the main data.
    """
    st.markdown("### Localização de Parceiros")
    st.caption("Filtre parceiros ativos (com contratos assinados) por Estado e Cidade.")

    if dados_df.empty:
        st.info("Nenhum dado de parceiros disponível.")
        return

    # Filter for "ASSINADO" status
    # Ensure column exists
    if C.COL_INT_STATUS not in dados_df.columns:
        st.warning(f"Coluna de status '{C.COL_INT_STATUS}' não encontrada nos dados.")
        return

    # Filter active partners (ASSINADO)
    # We use the internal column name for status
    active_mask = dados_df[C.COL_INT_STATUS] == C.STATUS_ASSINADO
    df_active = dados_df[active_mask]

    if df_active.empty:
        st.info("Nenhum parceiro com contrato assinado encontrado.")
        return

    # Select relevant columns: Partner, City, State
    cols_to_keep = [C.COL_INT_PARTNER, C.COL_INT_CITY, C.COL_INT_STATE]
    # Check if columns exist
    missing_cols = [c for c in cols_to_keep if c not in df_active.columns]
    if missing_cols:
        st.warning(f"Colunas faltando para localização: {missing_cols}")
        return

    # Get unique partners per location
    # A partner might appear multiple times (once per contract), so we drop duplicates
    df_unique = df_active[cols_to_keep].drop_duplicates()

    # Sort by State, then City, then Partner
    df_unique = df_unique.sort_values([C.COL_INT_STATE, C.COL_INT_CITY, C.COL_INT_PARTNER])

    # --- Filters ---
    col_filter1, col_filter2 = st.columns(2)

    # State Filter
    available_states = sorted(df_unique[C.COL_INT_STATE].dropna().unique())
    selected_states = col_filter1.multiselect("Filtrar por Estado", options=available_states)

    # City Filter (dependent on State)
    if selected_states:
        df_filtered_state = df_unique[df_unique[C.COL_INT_STATE].isin(selected_states)]
        available_cities = sorted(df_filtered_state[C.COL_INT_CITY].dropna().unique())
    else:
        df_filtered_state = df_unique
        available_cities = sorted(df_unique[C.COL_INT_CITY].dropna().unique())
    
    selected_cities = col_filter2.multiselect("Filtrar por Cidade", options=available_cities)

    # Apply Filters
    df_final = df_filtered_state
    if selected_cities:
        df_final = df_final[df_final[C.COL_INT_CITY].isin(selected_cities)]

    # Display Count
    st.write(f"**Parceiros encontrados:** {len(df_final)}")

    # Display Table
    # Rename columns for display
    display_df = df_final.rename(columns={
        C.COL_INT_PARTNER: "Parceiro",
        C.COL_INT_CITY: "Cidade",
        C.COL_INT_STATE: "Estado"
    })

    st.dataframe(display_df, use_container_width=True, hide_index=True)


def render(fat_df: pd.DataFrame, dados_df: pd.DataFrame, access_key: str):
    """
    Renders the Partners Analysis tab.

    Args:
        fat_df (pd.DataFrame): DataFrame containing financial/sales data.
        dados_df (pd.DataFrame): DataFrame containing main data (for location filtering).
        access_key (str): The access key required to view this tab.
    """
    if not _check_authentication(access_key):
        return

    st.markdown(C.UI_LABEL_PARTNERS_RANKING_TITLE)

    if fat_df.empty:
        st.info(C.UI_LABEL_NO_REVENUE_DATA)
        # Even if financial data is empty, we might want to show the location filter if dados_df is present?
        # But the user asked for it "below Ranking". 
        # If ranking is empty, we probably just return (as per original code).
        # However, let's allow it to proceed if we have dados_df, but maybe keep the original logic for now.
        # Original logic returns if fat_df is empty.
        # Let's keep it consistent: if no financial data, maybe no partners to show in ranking, but directory exists?
        # I'll stick to original flow for Ranking, then add Location section.
        # If fat_df is empty, the function returns. I should probably allow it to continue if dados_df is not empty.
        # But let's follow the user's "below Ranking" instruction literally.
    
    # Original Ranking Logic
    if not fat_df.empty:
        partner_sales = _aggregate_partner_sales(fat_df)

        if partner_sales.empty:
            st.info(C.UI_LABEL_NO_PARTNERS_FOUND)
        else:
            _render_sales_chart(partner_sales)
            st.divider()
            _render_revenue_chart(partner_sales)
            _render_partner_pareto(partner_sales)
            _render_partner_ticket_volume_scatter(partner_sales)
            st.divider()
            _render_summary_metrics(partner_sales)
            st.divider()
            _render_detailed_table(partner_sales)
    
    # New Location Filter Section
    if dados_df is not None and not dados_df.empty:
        st.divider()
        _render_partner_location_filter(dados_df)

