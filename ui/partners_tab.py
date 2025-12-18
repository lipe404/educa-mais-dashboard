import streamlit as st
import pandas as pd
import plotly.express as px
import os
from dotenv import load_dotenv
import constants as C

load_dotenv()
API_KEY = os.getenv("KEY_API")


def render(fat_df: pd.DataFrame):
    key = st.text_input(C.UI_LABEL_ACCESS_KEY, type="password", key="partners_access_key")
    if key != API_KEY:
        st.warning(C.UI_LABEL_ENTER_KEY_MSG)
        return

    st.markdown(C.UI_LABEL_PARTNERS_RANKING_TITLE)

    if fat_df.empty:
        st.info(C.UI_LABEL_NO_REVENUE_DATA)
        return

    # Aggregate data by partner
    partner_sales = fat_df.groupby(C.COL_INT_PARTNER).agg(
        total_vendas=(C.COL_INT_VALOR, 'count'),
        total_faturamento=(C.COL_INT_VALOR, 'sum')
    ).reset_index()

    # Filter out empty partners
    partner_sales = partner_sales[partner_sales[C.COL_INT_PARTNER] != ""]

    if partner_sales.empty:
        st.info(C.UI_LABEL_NO_PARTNERS_FOUND)
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
        title=C.UI_LABEL_TOP_10_SALES,
        labels={C.COL_INT_PARTNER: C.UI_LABEL_PARTNER, 'total_vendas': C.UI_LABEL_NUM_SALES},
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
        title=C.UI_LABEL_TOP_10_REVENUE,
        labels={C.COL_INT_PARTNER: C.UI_LABEL_PARTNER, 'total_faturamento': C.UI_LABEL_TOTAL_REVENUE_CURRENCY},
        color='total_faturamento',
        color_continuous_scale=px.colors.sequential.Blues,
        text_auto='.2f'
    )
    fig_revenue.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_revenue, width="stretch")

    # Summary metrics
    col1, col2, col3 = st.columns(3)
    col1.metric(C.UI_LABEL_TOTAL_PARTNERS, len(partner_sales))
    col2.metric(C.UI_LABEL_PARTNER_MOST_SALES, top_sales.iloc[0][C.COL_INT_PARTNER])
    col3.metric(C.UI_LABEL_PARTNER_MOST_REVENUE, top_revenue.iloc[0][C.COL_INT_PARTNER])


    # Detailed table
    st.markdown(C.UI_LABEL_PARTNERS_DETAILS_TITLE)
    table_df = partner_sales.rename(columns={
        C.COL_INT_PARTNER: C.UI_LABEL_PARTNER,
        'total_vendas': C.UI_LABEL_NUM_SALES,
        'total_faturamento': C.UI_LABEL_TOTAL_REVENUE_CURRENCY
    }).reset_index(drop=True)
    table_df[C.UI_LABEL_TOTAL_REVENUE_CURRENCY] = table_df[C.UI_LABEL_TOTAL_REVENUE_CURRENCY].apply(lambda x: f"R$ {x:,.2f}")
    st.dataframe(table_df)
