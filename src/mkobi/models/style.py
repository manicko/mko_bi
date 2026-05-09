"""Pydantic models for component styling.

Used for validating component style configuration.
"""

from pydantic import BaseModel, Field


class ComponentStyle(BaseModel):
    """Base component style model."""

    width: int = 12
    height: int | None = None
    className: str = ""
    shadow: bool = True
    margin: str = ""
    padding: str = ""


class ButtonStyle(ComponentStyle):
    """Style for buttons."""

    variant: str = "primary"
    size: str = ""
    outline: bool = False
    disabled: bool = False
    block: bool = True


class FilterStyle(ComponentStyle):
    """Style for filters."""

    label_width: int = 3
    control_width: int = 9
    inline: bool = False
    show_label: bool = True


class ChartStyle(ComponentStyle):
    """Style for charts."""

    graph_height: int = 400
    show_legend: bool = True
    colorway: list[str] = Field(default_factory=list)
    template: str = "plotly"
