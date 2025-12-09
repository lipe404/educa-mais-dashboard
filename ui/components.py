import plotly.graph_objects as go
import constants as C


def gauge_chart(value: float, target: float, title: str) -> go.Figure:
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value,
            title={"text": title},
            gauge={
                "axis": {"range": [0, target]},
                "bar": {"color": C.COLOR_SECONDARY},
                "bgcolor": C.COLOR_BG_DARK,
            },
        )
    )
    fig.update_layout(height=250, margin=dict(l=10, r=10, t=40, b=10))
    return fig

