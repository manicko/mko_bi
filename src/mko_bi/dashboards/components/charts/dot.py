import plotly.graph_objects as go
from typing import Dict, Any, Optional


def build_dot_chart(
    data: Dict[str, Any],
    x: str,
    y: str,
    size: Optional[str] = None,
    color: Optional[str] = None,
) -> go.Figure:
    """Build a dot (scatter) chart using Plotly.

    Args:
        data: Data dictionary with chart data
        x: Column name for x-axis
        y: Column name for y-axis
        size: Optional column for point sizing
        color: Optional column for point coloring

    Returns:
        Plotly Figure object
    """
    trace_kwargs = {
        "x": data[x],
        "y": data[y],
        "mode": "markers",
    }

    if size:
        trace_kwargs["marker_size"] = data[size]

    if color:
        trace_kwargs["marker_color"] = data[color]

    fig = go.Figure(data=[go.Scatter(**trace_kwargs)])

    fig.update_layout(xaxis_title=x, yaxis_title=y, showlegend=False)

    return fig
