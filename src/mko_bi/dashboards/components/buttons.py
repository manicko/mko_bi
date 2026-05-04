"""Компоненты кнопок для дашбордов.

Используются варианты ButtonVariant из mko_bi.models.enums.
"""

import logging
from typing import Any

import dash_bootstrap_components as dbc

from mko_bi.models.enums import ButtonVariant
from mko_bi.models.style import ButtonStyle

logger = logging.getLogger(__name__)


def create_button(
    text: str,
    variant: ButtonVariant | str = ButtonVariant.PRIMARY,
    id: str | dict[str, Any] | None = None,
    **kwargs: Any,
) -> dbc.Button:
    """Создание кнопки с заданным вариантом.

    Args:
        text: Текст кнопки
        variant: Вариант стиля кнопки
        id: Идентификатор кнопки
        **kwargs: Дополнительные параметры

    Returns:
        Объект dbc.Button
    """
    variant_str = variant.value if isinstance(variant, ButtonVariant) else variant
    logger.debug("Создание кнопки: '%s' (variant: %s)", text, variant_str)

    button_props: dict[str, Any] = {
        "color": variant_str,
        "children": text,
        **kwargs,
    }

    if id is not None:
        button_props["id"] = id

    return dbc.Button(**button_props)


def create_primary_button(
    text: str,
    id: str | dict[str, Any] | None = None,
    **kwargs: Any,
) -> dbc.Button:
    """Создание primary кнопки.

    Args:
        text: Текст кнопки
        id: Идентификатор кнопки
        **kwargs: Дополнительные параметры

    Returns:
        Объект dbc.Button
    """
    logger.debug("Создание primary кнопки: '%s'", text)
    return create_button(text, ButtonVariant.PRIMARY, id, **kwargs)


def create_secondary_button(
    text: str,
    id: str | dict[str, Any] | None = None,
    **kwargs: Any,
) -> dbc.Button:
    """Создание secondary кнопки.

    Args:
        text: Текст кнопки
        id: Идентификатор кнопки
        **kwargs: Дополнительные параметры

    Returns:
        Объект dbc.Button
    """
    logger.debug("Создание secondary кнопки: '%s'", text)
    return create_button(text, ButtonVariant.SECONDARY, id, **kwargs)


def create_success_button(
    text: str,
    id: str | dict[str, Any] | None = None,
    **kwargs: Any,
) -> dbc.Button:
    """Создание success кнопки.

    Args:
        text: Текст кнопки
        id: Идентификатор кнопки
        **kwargs: Дополнительные параметры

    Returns:
        Объект dbc.Button
    """
    logger.debug("Создание success кнопки: '%s'", text)
    return create_button(text, ButtonVariant.SUCCESS, id, **kwargs)


def create_danger_button(
    text: str,
    id: str | dict[str, Any] | None = None,
    **kwargs: Any,
) -> dbc.Button:
    """Создание danger кнопки.

    Args:
        text: Текст кнопки
        id: Идентификатор кнопки
        **kwargs: Дополнительные параметры

    Returns:
        Объект dbc.Button
    """
    logger.debug("Создание danger кнопки: '%s'", text)
    return create_button(text, ButtonVariant.DANGER, id, **kwargs)


def create_button_group(
    buttons: list[dbc.Button],
    vertical: bool = False,
    **kwargs: Any,
) -> dbc.ButtonGroup:
    """Создание группы кнопок.

    Args:
        buttons: Список кнопок
        vertical: Вертикальная группа
        **kwargs: Дополнительные параметры

    Returns:
        Объект dbc.ButtonGroup
    """
    logger.debug("Создание группы из %d кнопок", len(buttons))
    return dbc.ButtonGroup(
        buttons,
        vertical=vertical,
        **kwargs,
    )


def create_styled_button(
    text: str,
    style_config: ButtonStyle,
    id: str | dict[str, Any] | None = None,
) -> dbc.Button:
    """Создание кнопки с конфигурацией стиля.

    Args:
        text: Текст кнопки
        style_config: Конфигурация стиля
        id: Идентификатор кнопки

    Returns:
        Объект dbc.Button
    """
    logger.debug(
        "Создание стилизованной кнопки: '%s' (variant: %s)",
        text,
        style_config.variant,
    )

    button_props: dict[str, Any] = {
        "color": style_config.variant,
        "children": text,
        "outline": style_config.outline,
        "disabled": style_config.disabled,
        "block": style_config.block,
    }

    if style_config.size:
        button_props["size"] = style_config.size

    if id is not None:
        button_props["id"] = id

    return dbc.Button(**button_props)
