import streamlit as st
import plotly.express as px
import constants as C
import forecasting


def render(df):
    st.markdown("### Previsão de Contratos")

    c1, c2 = st.columns(2)
    with c1:
        algo = st.selectbox("Algoritmo", ["Prophet (Facebook AI)", "Holt-Winters (Sazonal)"])
    with c2:
        horizon_label = st.selectbox("Horizonte", ["1 Semana", "2 Semanas", "3 Semanas", "1 Mês", "3 Meses", "6 Meses", "1 Ano"])

    horizon_map = {"1 Semana": 7, "2 Semanas": 14, "3 Semanas": 21, "1 Mês": 30, "3 Meses": 90, "6 Meses": 180, "1 Ano": 365}
    days = horizon_map[horizon_label]

    signed_df = df[df[C.COL_INT_STATUS] == C.STATUS_ASSINADO].copy()
    df_input = signed_df.copy()
    df_input["Contratos"] = 1

    try:
        final_df = forecasting.generate_forecast(df_input, C.COL_INT_DT, "Contratos", algo, days)
        future_mask = final_df["Type"] == "Previsão"
        total_predicted = int(final_df[future_mask]["Contratos"].sum())
        total_historical = len(signed_df)
        total_final = total_historical + total_predicted

        m1, m2 = st.columns(2)
        m1.metric(label=f"Novos Contratos ({horizon_label})", value=total_predicted)
        m2.metric(label="Total Final Esperado", value=total_final, delta=f"+{total_predicted} novos")

        fig = px.line(final_df, x=C.COL_INT_DT, y="Contratos", color="Type", title=f"Previsão de Novos Contratos Diários - {algo}", color_discrete_map={"Histórico": C.COLOR_PRIMARY, "Previsão": C.COLOR_FORECAST})
        st.plotly_chart(fig, width="stretch")

        st.markdown("---")
        insights = forecasting.generate_smart_insights(df_input, C.COL_INT_DT, "Contratos", final_df)
        st.info(insights)
    except Exception as e:
        st.error(f"Erro ao gerar previsão: {e}")
        if "não instalada" in str(e):
            st.warning("Dica: Verifique se as bibliotecas 'prophet' e 'statsmodels' estão instaladas.")

