import streamlit as st
import plotly.express as px
import constants as C
import forecasting


def render(contracts_df, faturamento_df):
    t1, t2 = st.tabs([C.TAB_NAME_CONTRACTS, C.TAB_NAME_FINANCIAL])

    with t1:
        c1, c2 = st.columns(2)
        with c1:
            algo = st.selectbox(
                C.UI_LABEL_ALGORITHM,
                [C.ALGORITHM_PROPHET, C.ALGORITHM_HOLT_WINTERS],
                key="forecast_algo_contracts",
            )
        with c2:
            horizon_label = st.selectbox(
                C.UI_LABEL_HORIZON,
                [
                    C.UI_LABEL_HORIZON_1W,
                    C.UI_LABEL_HORIZON_2W,
                    C.UI_LABEL_HORIZON_3W,
                    C.UI_LABEL_HORIZON_1M,
                    C.UI_LABEL_HORIZON_3M,
                    C.UI_LABEL_HORIZON_6M,
                    C.UI_LABEL_HORIZON_1Y,
                ],
                key="forecast_horizon_contracts",
            )
            
        # Backtesting Button
        run_bt = st.button("🧪 Rodar Backtest (Validar Precisão)", key="bt_contracts")

        horizon_map = {
            C.UI_LABEL_HORIZON_1W: 7,
            C.UI_LABEL_HORIZON_2W: 14,
            C.UI_LABEL_HORIZON_3W: 21,
            C.UI_LABEL_HORIZON_1M: 30,
            C.UI_LABEL_HORIZON_3M: 90,
            C.UI_LABEL_HORIZON_6M: 180,
            C.UI_LABEL_HORIZON_1Y: 365,
        }
        days = horizon_map[horizon_label]

        signed_df = contracts_df[
            contracts_df[C.COL_INT_STATUS] == C.STATUS_ASSINADO
        ].copy()
        df_input = signed_df.copy()
        df_input[C.UI_LABEL_CONTRACTS] = 1
        
        # --- Backtesting Logic ---
        if run_bt:
            st.divider()
            st.markdown("### 🧪 Resultados do Backtest (Últimos 30 dias)")
            try:
                with st.spinner("Rodando backtest..."):
                    bt_results = forecasting.run_backtest(
                        df_input, C.COL_INT_DT, C.UI_LABEL_CONTRACTS, algo, test_days=30
                    )
                
                if "error" in bt_results:
                    st.error(bt_results["error"])
                else:
                    b1, b2, b3 = st.columns(3)
                    b1.metric("MAE (Erro Médio Absoluto)", f"{bt_results['mae']:.2f}")
                    b2.metric("RMSE (Raiz do Erro Quadrático)", f"{bt_results['rmse']:.2f}")
                    b3.metric("MAPE (Erro % Médio)", f"{bt_results['mape']:.2f}%")
                    
                    st.caption(f"Treinado com dados até: {bt_results['train_last_date'].strftime('%d/%m/%Y')}")
                    
                    # Plot comparison
                    comp_df = bt_results["comparison_df"]
                    fig_bt = px.line(title="Realizado vs Previsto (Backtest)")
                    fig_bt.add_scatter(x=comp_df[C.COL_INT_DT], y=comp_df[f"{C.UI_LABEL_CONTRACTS}_actual"], name="Realizado", line=dict(color=C.COLOR_PRIMARY))
                    fig_bt.add_scatter(x=comp_df[C.COL_INT_DT], y=comp_df[f"{C.UI_LABEL_CONTRACTS}_predicted"], name="Previsto (Backtest)", line=dict(color=C.COLOR_SECONDARY, dash="dot"))
                    st.plotly_chart(fig_bt, width="stretch")
                    
            except Exception as e:
                st.error(f"Erro ao rodar backtest: {e}")
            st.divider()
        # -------------------------

        try:
            final_df = forecasting.generate_forecast(
                df_input, C.COL_INT_DT, C.UI_LABEL_CONTRACTS, algo, days
            )
            future_mask = final_df["Type"] == C.UI_LABEL_FORECAST
            total_predicted = int(final_df[future_mask][C.UI_LABEL_CONTRACTS].sum())
            total_historical = len(signed_df)
            total_final = total_historical + total_predicted

            m1, m2 = st.columns(2)
            m1.metric(label=f"{C.UI_LABEL_NEW_CONTRACTS} ({horizon_label})", value=total_predicted)
            m2.metric(
                label=C.UI_LABEL_TOTAL_EXPECTED,
                value=total_final,
                delta=f"+{total_predicted} novos",
            )

            fig = px.line(
                final_df,
                x=C.COL_INT_DT,
                y=C.UI_LABEL_CONTRACTS,
                color="Type",
                title=f"{C.UI_LABEL_FORECAST_CONTRACTS_TITLE} - {algo}",
                color_discrete_map={
                    C.UI_LABEL_HISTORY: C.COLOR_PRIMARY,
                    C.UI_LABEL_FORECAST: C.COLOR_FORECAST,
                },
            )
            st.plotly_chart(fig, width="stretch")

            st.markdown("---")
            insights = forecasting.generate_smart_insights(
                df_input, C.COL_INT_DT, C.UI_LABEL_CONTRACTS, final_df
            )
            st.info(insights)
        except Exception as e:
            st.error(f"{C.UI_LABEL_ERROR_FORECAST}: {e}")
            if "não instalada" in str(e):
                st.warning(
                    C.UI_LABEL_TIP_INSTALL
                )

    with t2:
        c1, c2 = st.columns(2)
        with c1:
            algo_f = st.selectbox(
                C.UI_LABEL_ALGORITHM,
                [C.ALGORITHM_PROPHET, C.ALGORITHM_HOLT_WINTERS],
                key="forecast_algo_faturamento",
            )
        with c2:
            horizon_label_f = st.selectbox(
                C.UI_LABEL_HORIZON,
                [
                    C.UI_LABEL_HORIZON_1W,
                    C.UI_LABEL_HORIZON_2W,
                    C.UI_LABEL_HORIZON_3W,
                    C.UI_LABEL_HORIZON_1M,
                    C.UI_LABEL_HORIZON_3M,
                    C.UI_LABEL_HORIZON_6M,
                    C.UI_LABEL_HORIZON_1Y,
                ],
                key="forecast_horizon_faturamento",
            )
            
        # Backtesting Button
        run_bt_f = st.button("🧪 Rodar Backtest (Validar Precisão)", key="bt_faturamento")

        horizon_map = {
            C.UI_LABEL_HORIZON_1W: 7,
            C.UI_LABEL_HORIZON_2W: 14,
            C.UI_LABEL_HORIZON_3W: 21,
            C.UI_LABEL_HORIZON_1M: 30,
            C.UI_LABEL_HORIZON_3M: 90,
            C.UI_LABEL_HORIZON_6M: 180,
            C.UI_LABEL_HORIZON_1Y: 365,
        }
        days_f = horizon_map[horizon_label_f]

        df_input_f = faturamento_df.dropna(
            subset=[C.COL_INT_DATA, C.COL_INT_VALOR]
        ).copy()
        
        # --- Backtesting Logic ---
        if run_bt_f:
            st.divider()
            st.markdown("### 🧪 Resultados do Backtest (Últimos 30 dias)")
            try:
                with st.spinner("Rodando backtest..."):
                    bt_results = forecasting.run_backtest(
                        df_input_f, C.COL_INT_DATA, C.COL_INT_VALOR, algo_f, test_days=30
                    )
                
                if "error" in bt_results:
                    st.error(bt_results["error"])
                else:
                    b1, b2, b3 = st.columns(3)
                    b1.metric("MAE (Erro Médio Absoluto)", f"R$ {bt_results['mae']:,.2f}")
                    b2.metric("RMSE (Raiz do Erro Quadrático)", f"R$ {bt_results['rmse']:,.2f}")
                    b3.metric("MAPE (Erro % Médio)", f"{bt_results['mape']:.2f}%")
                    
                    st.caption(f"Treinado com dados até: {bt_results['train_last_date'].strftime('%d/%m/%Y')}")
                    
                    # Plot comparison
                    comp_df = bt_results["comparison_df"]
                    fig_bt = px.line(title="Realizado vs Previsto (Backtest)")
                    fig_bt.add_scatter(x=comp_df[C.COL_INT_DATA], y=comp_df[f"{C.COL_INT_VALOR}_actual"], name="Realizado", line=dict(color=C.COLOR_PRIMARY))
                    fig_bt.add_scatter(x=comp_df[C.COL_INT_DATA], y=comp_df[f"{C.COL_INT_VALOR}_predicted"], name="Previsto (Backtest)", line=dict(color=C.COLOR_SECONDARY, dash="dot"))
                    st.plotly_chart(fig_bt, width="stretch")
                    
            except Exception as e:
                st.error(f"Erro ao rodar backtest: {e}")
            st.divider()
        # -------------------------

        try:
            final_df_f = forecasting.generate_forecast(
                df_input_f, C.COL_INT_DATA, C.COL_INT_VALOR, algo_f, days_f
            )
            future_mask_f = final_df_f["Type"] == C.UI_LABEL_FORECAST
            total_predicted_f = float(
                final_df_f.loc[future_mask_f, C.COL_INT_VALOR].sum()
            )
            total_historical_f = float(df_input_f[C.COL_INT_VALOR].sum())
            total_final_f = total_historical_f + total_predicted_f

            m1, m2 = st.columns(2)
            m1.metric(
                label=f"{C.UI_LABEL_FORECAST_REVENUE} ({horizon_label_f})",
                value=f"R$ {total_predicted_f:,.2f}",
            )
            m2.metric(
                label=C.UI_LABEL_TOTAL_EXPECTED,
                value=f"R$ {total_final_f:,.2f}",
                delta=f"+R$ {total_predicted_f:,.2f}",
            )

            fig_f = px.line(
                final_df_f,
                x=C.COL_INT_DATA,
                y=C.COL_INT_VALOR,
                color="Type",
                title=f"{C.UI_LABEL_FORECAST_REVENUE_TITLE} - {algo_f}",
                color_discrete_map={
                    C.UI_LABEL_HISTORY: C.COLOR_PRIMARY,
                    C.UI_LABEL_FORECAST: C.COLOR_FORECAST,
                },
            )
            st.plotly_chart(fig_f, width="stretch")

            st.markdown("---")
            insights_f = forecasting.generate_smart_insights(
                df_input_f,
                C.COL_INT_DATA,
                C.COL_INT_VALOR,
                final_df_f,
                is_currency=True,
            )
            st.info(insights_f)
        except Exception as e:
            st.error(f"{C.UI_LABEL_ERROR_FORECAST}: {e}")
            if "não instalada" in str(e):
                st.warning(
                    C.UI_LABEL_TIP_INSTALL
                )
