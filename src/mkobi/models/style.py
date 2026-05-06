"""Pydantic модели для стилизации компонентов.

Используются для валидации конфигурации стилей компонентов.
"""

from pydantic import BaseModel, Field


class ComponentStyle(BaseModel):
    """Базовая модель стилей компонента."""

    width: int = 12
    height: int | None = None
    className: str = ""
    shadow: bool = True
    margin: str = ""
    padding: str = ""


class ButtonStyle(ComponentStyle):
    """Стиль для кнопок."""

    variant: str = "primary"
    size: str = ""
    outline: bool = False
    disabled: bool = False
    block: bool = True


class FilterStyle(ComponentStyle):
    """Стиль для фильтров."""

    label_width: int = 3
    control_width: int = 9
    inline: bool = False
    show_label: bool = True


class ChartStyle(ComponentStyle):
    """Стиль для графиков."""

    graph_height: int = 400
    show_legend: bool = True
    colorway: list[str] = Field(default_factory=list)
    template: str = "plotly"
