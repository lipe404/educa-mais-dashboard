import streamlit as st
import plotly.express as px
import constants as C
import forecasting


def render(contracts_df, faturamento_df):
    t1, t2 = st.tabs(["Contratos", "Faturamento"])

    with t1:
        c1, c2 = st.columns(2)
        with c1:
            algo = st.selectbox("Algoritmo", ["Prophet (Facebook AI)", "Holt-Winters (Sazonal)"], key="forecast_algo_contracts")
        with c2:
            horizon_label = st.selectbox("Horizonte", ["1 Semana", "2 Semanas", "3 Semanas", "1 Mês", "3 Meses", "6 Meses", "1 Ano"], key="forecast_horizon_contracts")

        horizon_map = {"1 Semana": 7, "2 Semanas": 14, "3 Semanas": 21, "1 Mês": 30, "3 Meses": 90, "6 Meses": 180, "1 Ano": 365}
        days = horizon_map[horizon_label]

        signed_df = contracts_df[contracts_df[C.COL_INT_STATUS] == C.STATUS_ASSINADO].copy()
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

    with t2:
        c1, c2 = st.columns(2)
        with c1:
            algo_f = st.selectbox("Algoritmo", ["Prophet (Facebook AI)", "Holt-Winters (Sazonal)"], key="forecast_algo_faturamento")
        with c2:
            horizon_label_f = st.selectbox("Horizonte", ["1 Semana", "2 Semanas", "3 Semanas", "1 Mês", "3 Meses", "6 Meses", "1 Ano"], key="forecast_horizon_faturamento")

        horizon_map = {"1 Semana": 7, "2 Semanas": 14, "3 Semanas": 21, "1 Mês": 30, "3 Meses": 90, "6 Meses": 180, "1 Ano": 365}
        days_f = horizon_map[horizon_label_f]

        df_input_f = faturamento_df.dropna(subset=[C.COL_INT_DATA, C.COL_INT_VALOR]).copy()

        try:
            final_df_f = forecasting.generate_forecast(df_input_f, C.COL_INT_DATA, C.COL_INT_VALOR, algo_f, days_f)
            future_mask_f = final_df_f["Type"] == "Previsão"
            total_predicted_f = float(final_df_f.loc[future_mask_f, C.COL_INT_VALOR].sum())
            total_historical_f = float(df_input_f[C.COL_INT_VALOR].sum())
            total_final_f = total_historical_f + total_predicted_f

            m1, m2 = st.columns(2)
            m1.metric(label=f"Faturamento previsto ({horizon_label_f})", value=f"R$ {total_predicted_f:,.2f}")
            m2.metric(label="Total final esperado", value=f"R$ {total_final_f:,.2f}", delta=f"+R$ {total_predicted_f:,.2f}")

            fig_f = px.line(final_df_f, x=C.COL_INT_DATA, y=C.COL_INT_VALOR, color="Type", title=f"Previsão de Faturamento Diário - {algo_f}", color_discrete_map={"Histórico": C.COLOR_PRIMARY, "Previsão": C.COLOR_FORECAST})
            st.plotly_chart(fig_f, width="stretch")

            st.markdown("---")
            daily_f = df_input_f.groupby(df_input_f[C.COL_INT_DATA].dt.date)[C.COL_INT_VALOR].sum().sort_index()
            if len(daily_f) >= 14:
                recent_avg_f = daily_f.tail(7).mean()
                prev_avg_f = daily_f.iloc[-14:-7].mean()
                trend_pct_f = ((recent_avg_f - prev_avg_f) / prev_avg_f * 100) if prev_avg_f > 0 else 0
                future_only_f = final_df_f[final_df_f["Type"] == "Previsão"]
                future_sum_f = float(future_only_f[C.COL_INT_VALOR].sum())
                future_daily_avg_f = float(future_only_f[C.COL_INT_VALOR].mean())
                horizon_days_f = len(future_only_f)
                txt = "### 🧠 Análise Inteligente\n\n"
                if trend_pct_f > 5:
                    emoji = "🚀"
                    trend_desc = "Crescimento de faturamento"
                elif trend_pct_f < -5:
                    emoji = "⚠️"
                    trend_desc = "Queda recente de faturamento"
                else:
                    emoji = "⚖️"
                    trend_desc = "Estabilidade de faturamento"
                txt += f"**Tendência Recente (7 dias):** {trend_desc} ({trend_pct_f:+.1f}%) {emoji}\n\n"
                txt += f"**Previsão para os próximos {horizon_days_f} dias:**\n"
                txt += f"- **Total estimado:** R$ {future_sum_f:,.2f}\n"
                txt += f"- **Média diária esperada:** R$ {future_daily_avg_f:,.2f}/dia\n\n"
                if future_daily_avg_f > recent_avg_f * 1.05:
                    txt += "> **Insight:** O modelo prevê avanço do faturamento."
                elif future_daily_avg_f < recent_avg_f * 0.9:
                    txt += "> **Insight:** O modelo prevê leve queda."
                else:
                    txt += "> **Insight:** Ritmo de faturamento estável."
                st.info(txt)
            else:
                st.info("Dados insuficientes para análise detalhada (mínimo 2 semanas).")
        except Exception as e:
            st.error(f"Erro ao gerar previsão: {e}")
            if "não instalada" in str(e):
                st.warning("Dica: Verifique se as bibliotecas 'prophet' e 'statsmodels' estão instaladas.")
