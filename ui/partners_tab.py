import streamlit as st
import pandas as pd
import plotly.express as px
import os
from dotenv import load_dotenv
import constants as C

load_dotenv()
API_KEY = os.getenv("KEY_API")


def render(fat_df: pd.DataFrame):
    key = st.text_input("Chave de acesso", type="password", key="partners_access_key")
    if key != API_KEY:
        st.warning("Digite a chave de acesso para visualizar a análise.")
        return

    st.markdown("### Ranking de Parceiros por Vendas e Faturamento")

    if fat_df.empty:
        st.info("Nenhum dado de faturamento disponível.")
        return

    # Aggregate data by partner
    partner_sales = fat_df.groupby(C.COL_INT_PARTNER).agg(
        total_vendas=(C.COL_INT_VALOR, 'count'),
        total_faturamento=(C.COL_INT_VALOR, 'sum')
    ).reset_index()

    # Filter out empty partners
    partner_sales = partner_sales[partner_sales[C.COL_INT_PARTNER] != ""]

    if partner_sales.empty:
        st.info("Nenhum parceiro encontrado nos dados.")
        return

    # Sort by total sales (descending)
    partner_sales = partner_sales.sort_values('total_vendas', ascending=False)

    # Top 10 by sales
    top_sales = partner_sales.head(10)

    # Chart for ranking by number of sales
    fig_sales = px.bar(
        top_sales,
        x=C.COL_INT_PARTNER,
        y='total_vendas',
        title="Top 10 Parceiros por Número de Vendas",
        labels={C.COL_INT_PARTNER: "Parceiro", 'total_vendas': "Número de Vendas"},
        color='total_vendas',
        color_continuous_scale=px.colors.sequential.Pinkyl,
        text_auto=True
    )
    fig_sales.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_sales, width="stretch")

    # Sort by total revenue (descending)
    partner_sales_rev = partner_sales.sort_values('total_faturamento', ascending=False)

    # Top 10 by revenue
    top_revenue = partner_sales_rev.head(10)

    # Chart for ranking by total revenue
    fig_revenue = px.bar(
        top_revenue,
        x=C.COL_INT_PARTNER,
        y='total_faturamento',
        title="Top 10 Parceiros por Faturamento Total",
        labels={C.COL_INT_PARTNER: "Parceiro", 'total_faturamento': "Faturamento Total (R$)"},
        color='total_faturamento',
        color_continuous_scale=px.colors.sequential.Blues,
        text_auto='.2f'
    )
    fig_revenue.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_revenue, width="stretch")

    # Summary metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Parceiros", len(partner_sales))
    col2.metric("Parceiro com Mais Vendas", top_sales.iloc[0][C.COL_INT_PARTNER])
    col3.metric("Parceiro com Maior Faturamento", top_revenue.iloc[0][C.COL_INT_PARTNER])


    # Detailed table
    st.markdown("### Detalhes dos Parceiros")
    table_df = partner_sales.rename(columns={
        C.COL_INT_PARTNER: "Parceiro",
        'total_vendas': "Número de Vendas",
        'total_faturamento': "Faturamento Total (R$)"
    }).reset_index(drop=True)
    table_df['Faturamento Total (R$)'] = table_df['Faturamento Total (R$)'].apply(lambda x: f"R$ {x:,.2f}")
    st.dataframe(table_df)
