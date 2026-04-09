import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import constants as C
from typing import Callable, Any, Dict

try:
    from statsmodels.tsa.seasonal import seasonal_decompose

    STATSMODELS_DECOMP_AVAILABLE = True
except Exception:
    seasonal_decompose = None
    STATSMODELS_DECOMP_AVAILABLE = False


def _render_series_decomposition(
    df: "pd.DataFrame",
    date_col: str,
    value_col: str,
    title_prefix: str,
    is_currency: bool,
) -> None:
    if not STATSMODELS_DECOMP_AVAILABLE:
        st.warning(C.UI_LABEL_TIP_INSTALL)
        return

    if df is None or df.empty:
        return
    if date_col not in df.columns or value_col not in df.columns:
        return

    base = df[[date_col, value_col]].copy()
    base[date_col] = pd.to_datetime(base[date_col], errors="coerce")
    base[value_col] = pd.to_numeric(base[value_col], errors="coerce")
    base = base.dropna(subset=[date_col, value_col])
    if base.empty:
        return

    daily = base.groupby(base[date_col].dt.date)[value_col].sum().reset_index()
    daily[date_col] = pd.to_datetime(daily[date_col])
    daily = daily.sort_values(date_col)

    idx = pd.date_range(daily[date_col].min(), daily[date_col].max(), freq="D")
    daily = daily.set_index(date_col).reindex(idx, fill_value=0).reset_index()
    daily = daily.rename(columns={"index": date_col})
    series = daily[value_col].astype(float)

    freq_choice = st.radio(
        "Sazonalidade para decomposição",
        ["Semanal (7 dias)", "Mensal (30 dias)"],
        horizontal=True,
        key=f"decomp_freq_{title_prefix}_{date_col}_{value_col}",
    )
    period = 7 if "Semanal" in freq_choice else 30
    if len(series) < period * 2:
        st.info(
            f"Dados insuficientes para decompor com período {period}. Necessário pelo menos {period*2} dias."
        )
        return

    try:
        res = seasonal_decompose(series, model="additive", period=period, extrapolate_trend="freq")
    except Exception as e:
        st.error(f"Erro ao decompor série: {e}")
        return

    st.markdown("### Decomposição de série temporal (tendência + sazonalidade + resíduo)")
    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.04,
        subplot_titles=("Tendência (longo prazo)", "Sazonalidade", "Resíduo (ruído)"),
    )
    x = daily[date_col]
    fig.add_trace(
        go.Scatter(
            x=x,
            y=series,
            mode="lines",
            name="Observado",
            line=dict(color="rgba(255,255,255,0.25)", width=1),
            hovertemplate="%{x|%d/%m/%Y}<br>%{y:,.2f}<extra></extra>",
            connectgaps=True,
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=x,
            y=res.trend,
            mode="lines",
            name="Tendência",
            line=dict(color=C.COLOR_PRIMARY, width=2),
            hovertemplate="%{x|%d/%m/%Y}<br>%{y:,.2f}<extra></extra>",
            connectgaps=True,
        ),
        row=1,
        col=1,
    )

    if period == 7:
        seasonal_df = pd.DataFrame({"dow": x.dt.dayofweek, "seasonal": res.seasonal})
        seasonal_profile = seasonal_df.groupby("dow")["seasonal"].mean().reindex(list(range(7)))
        seasonal_x = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
    else:
        seasonal_df = pd.DataFrame({"dom": x.dt.day, "seasonal": res.seasonal})
        seasonal_profile = seasonal_df.groupby("dom")["seasonal"].mean().reindex(list(range(1, 32)))
        seasonal_x = [str(i) for i in range(1, 32)]

    fig.add_trace(
        go.Bar(
            x=seasonal_x,
            y=seasonal_profile.to_numpy(),
            name="Sazonalidade (perfil)",
            marker_color=C.COLOR_SECONDARY,
            hovertemplate="%{x}<br>%{y:,.2f}<extra></extra>",
        ),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=x,
            y=res.resid,
            mode="lines",
            name="Resíduo",
            line=dict(color="rgba(255,255,255,0.6)", width=1),
            hovertemplate="%{x|%d/%m/%Y}<br>%{y:,.2f}<extra></extra>",
            connectgaps=True,
        ),
        row=3,
        col=1,
    )
    fig.update_layout(
        title=f"{title_prefix}: decomposição (período {period} dias)",
        showlegend=False,
        margin=dict(l=10, r=10, t=70, b=10),
        height=700,
    )
    if is_currency:
        fig.update_yaxes(tickprefix="R$ ", tickformat=",.0f", row=1, col=1)
        fig.update_yaxes(tickprefix="R$ ", tickformat=",.2f", row=2, col=1)
        fig.update_yaxes(tickprefix="R$ ", tickformat=",.2f", row=3, col=1)
    st.plotly_chart(fig, width="stretch")


def _render_backtest_results(bt_results: Dict[str, Any], y_col: str, y_label: str, is_currency: bool = False):
    """
    Renders the backtest results including metrics (MAE, RMSE, MAPE) and a comparison chart.

    Args:
        bt_results (Dict[str, Any]): Dictionary containing backtest results and metrics.
        y_col (str): The name of the target column in the dataframe.
        y_label (str): Label for the target variable to be used in the chart.
        is_currency (bool, optional): If True, formats metrics as currency. Defaults to False.
    """
    if "error" in bt_results:
        st.error(bt_results["error"])
    else:
        b1, b2, b3 = st.columns(3)
        if is_currency:
            b1.metric("MAE (Erro Médio Absoluto)", f"R$ {bt_results['mae']:,.2f}")
            b2.metric("RMSE (Raiz do Erro Quadrático)", f"R$ {bt_results['rmse']:,.2f}")
        else:
            b1.metric("MAE (Erro Médio Absoluto)", f"{bt_results['mae']:.2f}")
            b2.metric("RMSE (Raiz do Erro Quadrático)", f"{bt_results['rmse']:.2f}")
        
        b3.metric("MAPE (Erro % Médio)", f"{bt_results['mape']:.2f}%")

        st.caption(
            f"Treinado com dados até: {bt_results['train_last_date'].strftime('%d/%m/%Y')}"
        )

        # Plot comparison
        comp_df = bt_results["comparison_df"]
        fig_bt = px.line(title="Realizado vs Previsto (Backtest)")
        fig_bt.add_scatter(
            x=comp_df[C.COL_INT_DT if C.COL_INT_DT in comp_df.columns else C.COL_INT_DATA],
            y=comp_df[f"{y_label}_actual"],
            name="Realizado",
            line=dict(color=C.COLOR_PRIMARY),
        )
        fig_bt.add_scatter(
            x=comp_df[C.COL_INT_DT if C.COL_INT_DT in comp_df.columns else C.COL_INT_DATA],
            y=comp_df[f"{y_label}_predicted"],
            name="Previsto (Backtest)",
            line=dict(color=C.COLOR_SECONDARY, dash="dot"),
        )
        st.plotly_chart(fig_bt, width="stretch")


def _render_forecast_results(
    final_df, 
    total_predicted, 
    total_final, 
    horizon_label, 
    algo, 
    x_col, 
    y_col, 
    y_label, 
    title, 
    is_currency=False
):
    """
    Renders the forecast results including key metrics and a line chart.

    Args:
        final_df (pd.DataFrame): DataFrame containing historical and forecasted data.
        total_predicted (float): Total predicted value for the forecast horizon.
        total_final (float): Total cumulative value (historical + predicted).
        horizon_label (str): Label describing the forecast horizon (e.g., "1 Month").
        algo (str): Name of the algorithm used for forecasting.
        x_col (str): Name of the date column.
        y_col (str): Name of the target variable column.
        y_label (str): Label for the target variable.
        title (str): Title for the forecast chart.
        is_currency (bool, optional): If True, formats values as currency. Defaults to False.
    """
    m1, m2 = st.columns(2)
    
    val_fmt = f"R$ {total_predicted:,.2f}" if is_currency else f"{int(total_predicted)}"
    final_fmt = f"R$ {total_final:,.2f}" if is_currency else f"{total_final}"
    delta_fmt = f"+{val_fmt}" if is_currency else f"+{val_fmt} novos"
    
    label_metric = f"{C.UI_LABEL_FORECAST_REVENUE}" if is_currency else f"{C.UI_LABEL_NEW_CONTRACTS}"

    m1.metric(
        label=f"{label_metric} ({horizon_label})",
        value=val_fmt,
    )
    m2.metric(
        label=C.UI_LABEL_TOTAL_EXPECTED,
        value=final_fmt,
        delta=delta_fmt,
    )

    st.divider()

    fig = px.line(
        final_df,
        x=x_col,
        y=y_col,
        color="Type",
        title=f"{title} - {algo}",
        color_discrete_map={
            C.UI_LABEL_HISTORY: C.COLOR_PRIMARY,
            C.UI_LABEL_FORECAST: C.COLOR_FORECAST,
        },
    )
    st.plotly_chart(fig, width="stretch")


def _render_contracts_tab(
    contracts_df,
    run_backtest: Callable,
    generate_forecast: Callable,
    generate_smart_insights: Callable,
):
    """
    Renders the Contracts forecasting sub-tab.

    Args:
        contracts_df (pd.DataFrame): DataFrame containing contracts data.
        run_backtest (Callable): Function to run backtesting.
        generate_forecast (Callable): Function to generate forecasts.
        generate_smart_insights (Callable): Function to generate smart insights from forecast data.
    """
    c1, c2 = st.columns(2)
    with c1:
        algo = st.selectbox(
            C.UI_LABEL_ALGORITHM,
            [C.ALGORITHM_PROPHET, C.ALGORITHM_HOLT_WINTERS, C.ALGORITHM_XGBOOST],
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
                bt_results = run_backtest(
                    df_input, C.COL_INT_DT, C.UI_LABEL_CONTRACTS, algo, test_days=30
                )
            _render_backtest_results(bt_results, C.COL_INT_DT, C.UI_LABEL_CONTRACTS, is_currency=False)

        except Exception as e:
            st.error(f"Erro ao rodar backtest: {e}")
        st.divider()
    # -------------------------

    try:
        final_df = generate_forecast(
            df_input, C.COL_INT_DT, C.UI_LABEL_CONTRACTS, algo, days
        )
        future_mask = final_df["Type"] == C.UI_LABEL_FORECAST
        total_predicted = int(final_df[future_mask][C.UI_LABEL_CONTRACTS].sum())
        total_historical = len(signed_df)
        total_final = total_historical + total_predicted

        _render_forecast_results(
            final_df, 
            total_predicted, 
            total_final, 
            horizon_label, 
            algo, 
            C.COL_INT_DT, 
            C.UI_LABEL_CONTRACTS, 
            C.UI_LABEL_CONTRACTS, 
            C.UI_LABEL_FORECAST_CONTRACTS_TITLE, 
            is_currency=False
        )

        st.divider()
        _render_series_decomposition(
            df_input,
            C.COL_INT_DT,
            C.UI_LABEL_CONTRACTS,
            "Contratos",
            is_currency=False,
        )
        st.divider()
        insights = generate_smart_insights(
            df_input, C.COL_INT_DT, C.UI_LABEL_CONTRACTS, final_df
        )
        st.info(insights)
    except Exception as e:
        st.error(f"{C.UI_LABEL_ERROR_FORECAST}: {e}")
        if "não instalada" in str(e):
            st.warning(C.UI_LABEL_TIP_INSTALL)


def _render_financial_tab(
    faturamento_df,
    run_backtest: Callable,
    generate_forecast: Callable,
    generate_smart_insights: Callable,
):
    """
    Renders the Financial forecasting sub-tab.

    Args:
        faturamento_df (pd.DataFrame): DataFrame containing financial data.
        run_backtest (Callable): Function to run backtesting.
        generate_forecast (Callable): Function to generate forecasts.
        generate_smart_insights (Callable): Function to generate smart insights from forecast data.
    """
    c1, c2 = st.columns(2)
    with c1:
        algo_f = st.selectbox(
            C.UI_LABEL_ALGORITHM,
            [C.ALGORITHM_PROPHET, C.ALGORITHM_HOLT_WINTERS, C.ALGORITHM_XGBOOST],
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
    run_bt_f = st.button(
        "🧪 Rodar Backtest (Validar Precisão)", key="bt_faturamento"
    )

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
                bt_results = run_backtest(
                    df_input_f,
                    C.COL_INT_DATA,
                    C.COL_INT_VALOR,
                    algo_f,
                    test_days=30,
                )
            _render_backtest_results(bt_results, C.COL_INT_DATA, C.COL_INT_VALOR, is_currency=True)

        except Exception as e:
            st.error(f"Erro ao rodar backtest: {e}")
        st.divider()
    # -------------------------

    try:
        final_df_f = generate_forecast(
            df_input_f, C.COL_INT_DATA, C.COL_INT_VALOR, algo_f, days_f
        )
        future_mask_f = final_df_f["Type"] == C.UI_LABEL_FORECAST
        total_predicted_f = float(
            final_df_f.loc[future_mask_f, C.COL_INT_VALOR].sum()
        )
        total_historical_f = float(df_input_f[C.COL_INT_VALOR].sum())
        total_final_f = total_historical_f + total_predicted_f

        _render_forecast_results(
            final_df_f, 
            total_predicted_f, 
            total_final_f, 
            horizon_label_f, 
            algo_f, 
            C.COL_INT_DATA, 
            C.COL_INT_VALOR, 
            C.COL_INT_VALOR, 
            C.UI_LABEL_FORECAST_REVENUE_TITLE, 
            is_currency=True
        )

        st.divider()
        _render_series_decomposition(
            df_input_f,
            C.COL_INT_DATA,
            C.COL_INT_VALOR,
            "Faturamento",
            is_currency=True,
        )
        st.divider()
        insights_f = generate_smart_insights(
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
            st.warning(C.UI_LABEL_TIP_INSTALL)


def render(
    contracts_df,
    faturamento_df,
    run_backtest: Callable,
    generate_forecast: Callable,
    generate_smart_insights: Callable,
):
    """
    Renders the main Forecast tab, containing sub-tabs for Contracts and Financial forecasting.

    Args:
        contracts_df (pd.DataFrame): DataFrame containing contracts data.
        faturamento_df (pd.DataFrame): DataFrame containing financial data.
        run_backtest (Callable): Function to run backtesting.
        generate_forecast (Callable): Function to generate forecasts.
        generate_smart_insights (Callable): Function to generate smart insights from forecast data.
    """
    t1, t2 = st.tabs([C.TAB_NAME_CONTRACTS, C.TAB_NAME_FINANCIAL])

    with t1:
        _render_contracts_tab(
            contracts_df, run_backtest, generate_forecast, generate_smart_insights
        )

    with t2:
        _render_financial_tab(
            faturamento_df, run_backtest, generate_forecast, generate_smart_insights
        )
