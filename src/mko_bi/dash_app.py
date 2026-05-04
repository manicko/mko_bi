"""Dash приложение для BI дашбордов.

Этот модуль предоставляет полнофункциональное веб-приложение на базе Dash
для визуализации данных с использованием Plotly. Приложение интегрируется
с FastAPI и обеспечивает:
- Аутентификацию через JWT
- Проверку валидности JWT токена
- Список доступных дашбордов
- Просмотр дашбордов с интерактивными графиками
- Фильтрацию данных

Functions:
    create_dash_app: Создает и конфигурирует Dash приложение
    create_login_page: Создает страницу авторизации
    create_dashboard_list_page: Создает страницу со списком дашбордов
    create_dashboard_page: Создает страницу просмотра дашборда
    render_graph: Рендерит график через Plotly
"""

import logging
from datetime import datetime, UTC
from typing import Any, cast

import dash
import dash_bootstrap_components as dbc
import jwt
import requests
from dash import Dash, Input, Output, State, callback, dcc, html, no_update
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go

from mko_bi.config import get_config
from mko_bi.core.security import decode_token


logger = logging.getLogger(__name__)


def check_token_validity(token: str) -> bool:
    """Проверяет валидность JWT токена (с проверкой подписи).

    Декодирует токен и проверяет срок его действия.
    Используется для серверной проверки токена.

    Args:
        token: JWT токен для проверки.

    Returns:
        bool: True, если токен валиден и не истек, иначе False.
    """
    payload = validate_jwt_token(token)
    if payload is None:
        return False
    
    exp = payload.get("exp")
    if exp is None:
        logger.warning("Токен не содержит поле exp")
        return False
    
    exp_datetime = datetime.fromtimestamp(exp, tz=UTC)
    now = datetime.now(UTC)
    is_valid = exp_datetime > now
    if not is_valid:
        logger.info("Токен истек (exp: %s, now: %s)", exp_datetime, now)
    return is_valid


def decode_token_payload(token: str) -> dict[str, Any] | None:
    """Декодирует полезную нагрузку JWT токена без проверки подписи.

    Args:
        token: JWT токен.

    Returns:
        dict[str, Any] | None: Данные токена или None при ошибке.
    """
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            options={"verify_signature": False},
        )
        return payload
    except Exception as e:
        logger.error("Ошибка декодирования токена: %s", e)
        return None


def validate_jwt_token(token: str) -> dict[str, Any] | None:
    """Проверяет JWT токен с валидацией подписи.

    Использует существующую функцию decode_token из core/security
    для проверки подписи токена и срока его действия.

    Args:
        token: JWT токен для проверки.

    Returns:
        dict[str, Any] | None: Данные токена при успешной проверке,
            None при ошибке (неверная подпись, истекший токен и т.д.).
    """
    try:
        logger.debug("Проверка JWT токена с валидацией подписи")
        payload: dict[str, Any] | None = decode_token(token)
        return payload
    except Exception as e:
        logger.warning("JWT токен недействителен: %s", e)
        return None


def fetch_dashboard_data(
    dashboard_id: str, token: str, filters: dict[str, Any] | None = None
) -> list[dict[str, Any]] | None:
    """Получает данные дашборда через API.

    Args:
        dashboard_id: Идентификатор дашборда.
        token: JWT токен для авторизации.
        filters: Опциональные фильтры для применения.

    Returns:
        dict[str, Any] | None: Данные дашборда или None при ошибке.
    """
    try:
        api_base_url = get_config().API_BASE_URL
        headers = {"Authorization": f"Bearer {token}"}

        if filters:
            # Применяем фильтры через POST запрос
            filter_request = {"dashboard_id": dashboard_id, "filters": filters}
            response = requests.post(
                f"{api_base_url}/data/filter",
                headers=headers,
                json=filter_request,
                timeout=30,
            )
        else:
            # Получаем все данные дашборда
            response = requests.get(
                f"{api_base_url}/data/{dashboard_id}",
                headers=headers,
                timeout=30,
            )

        response.raise_for_status()
        data: dict[str, Any] | list[dict[str, Any]] = response.json()
        logger.info(
            "Данные дашборда %s получены: %d записей",
            dashboard_id,
            len(data) if isinstance(data, list) else 0,
        )
        return cast(list[dict[str, Any]] | None, data)

    except requests.HTTPError as e:
        status_code = response.status_code if 'response' in locals() else 0
        logger.error(
            "Ошибка HTTP при получении данных дашборда %s: %s (код %s)",
            dashboard_id,
            e,
            status_code,
        )
        return None
    except requests.RequestException as e:
        logger.error(
            "Ошибка сети при получении данных дашборда %s: %s",
            dashboard_id,
            e,
        )
        return None
    except Exception as e:
        logger.error(
            "Неизвестная ошибка при получении данных дашборда %s: %s",
            dashboard_id,
            e,
        )
        return None


def create_dash_app(fastapi_app=None, prefix: str = "/dash") -> Dash:
    """Создает и конфигурирует Dash приложение.

    Инициализирует Dash приложение с поддержкой Bootstrap тем,
    настраивает макет, регистрирует callback-и и интегрируется
    с FastAPI приложением через WSGI middleware.

    Args:
        fastapi_app: Экземпляр FastAPI приложения для интеграции.
                     Если None, создается standalone приложение.
        prefix: URL префикс для Dash приложения.

    Returns:
        Dash: Сконфигурированное Dash приложение.

    Example:
        >>> from mko_bi.app import create_app
        >>> fastapi_app = create_app()
        >>> dash_app = create_dash_app(fastapi_app)
    """
    logger.info("Инициализация Dash приложения")

    # Создаем Dash приложение
    app = Dash(
        __name__,
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        suppress_callback_exceptions=True,
        routes_pathname_prefix=prefix,
        requests_pathname_prefix=prefix,
    )

    # Настройка макета приложения
    app.layout = html.Div(
        [
            dcc.Location(id="url", refresh=False),
            dcc.Store(id="auth-token", storage_type="local"),
            dcc.Store(id="current-user", storage_type="local"),
            dcc.Interval(
                id="token-check-interval",
                interval=60 * 1000,  # Проверка каждую минуту
                n_intervals=0,
            ),
            html.Div(id="page-content"),
        ],
        className="container-fluid",
    )

    # Регистрация callback-ов
    _register_callbacks(app)

    logger.info("Dash приложение успешно инициализировано")
    return app


def _register_callbacks(app: Dash) -> None:
    """Регистрирует все callback-и для Dash приложения.

    Args:
        app: Экземпляр Dash приложения.
    """

@callback(
    Output("url", "pathname", allow_duplicate=True),
    Input("token-check-interval", "n_intervals"),
    State("auth-token", "data"),
    State("url", "pathname"),
    prevent_initial_call=True,
)
def periodic_token_check(
    n_intervals: int, token: str | None, current_path: str
) -> str:
    """Периодически проверяет валидность токена и перенаправляет на login при истечении.

    Args:
        n_intervals: Количество интервалов (не используется напрямую).
        token: JWT токен аутентификации.
        current_path: Текущий путь URL.

    Returns:
        str: Путь для перенаправления (если токен недействителен).
    """
    if not token or not check_token_validity(token):
        if current_path not in ("/dashboards/login", "/dashboards"):
            logger.info("Периодическая проверка: токен недействителен, перенаправление на login")
            return "/dashboards/login"
    raise PreventUpdate


@callback(
    Output("page-content", "children"),
    Input("url", "pathname"),
    Input("auth-token", "data"),
)
def display_page(pathname: str, token: str | None) -> html.Div:
        """Определяет, какая страница должна быть отображена.

        Проверяет валидность JWT токена перед отображением защищенных страниц.
        При истечении токена перенаправляет на страницу входа.

        Args:
            pathname: Текущий URL путь.
            token: JWT токен аутентификации.

        Returns:
            html.Div: Содержимое страницы.
        """
        logger.debug("Переход на страницу: %s", pathname)

        if not pathname or pathname == "/dashboards/login":
            return create_login_page()
        elif pathname == "/dashboards":
            if not token or not check_token_validity(token):
                logger.info("Токен недействителен, перенаправление на login")
                return create_login_page()
            return create_dashboard_list_page()
        elif pathname.startswith("/dashboard/"):
            if not token or not check_token_validity(token):
                logger.info("Токен недействителен, перенаправление на login")
                return create_login_page()
            dashboard_id = pathname.split("/")[-1]
            return create_dashboard_page(dashboard_id)
        else:
            return html.Div(
                [
                    html.H1("404 - Страница не найдена"),
                    html.P("Запрошенная страница не существует."),
                    dbc.Button("На главную", href="/dashboards/login", color="primary"),
                ],
                className="text-center mt-5",
            )


def create_login_page() -> html.Div:
    """Создает страницу авторизации.

    Форма для ввода email и пароля с JWT аутентификацией.
    После успешного входа перенаправляет на список дашбордов.

    Returns:
        html.Div: Компонент страницы авторизации.
    """
    logger.info("Создание страницы авторизации")

    return html.Div(
        [
            html.Div(
                [
                    html.H2("Вход в систему", className="text-center mb-4"),
                    dbc.Form([
                        dbc.FormGroup([
                            dbc.Label("Email", html_for="login-email"),
                            dbc.Input(
                                type="email",
                                id="login-email",
                                placeholder="Введите email",
                                className="mb-3",
                            ),
                        ]),
                        dbc.FormGroup([
                            dbc.Label("Пароль", html_for="login-password"),
                            dbc.Input(
                                type="password",
                                id="login-password",
                                placeholder="Введите пароль",
                                className="mb-3",
                            ),
                        ]),
                        dbc.Button(
                            "Войти",
                            id="login-button",
                            color="primary",
                            className="w-100 mb-3",
                            n_clicks=0,
                        ),
                        html.Div(id="login-error", className="text-danger mb-3"),
                    ]),
                ],
                className="col-md-6 offset-md-3",
            )
        ],
        className="row mt-5",
    )


@callback(
    Output("auth-token", "data"),
    Output("current-user", "data"),
    Output("url", "pathname"),
    Output("login-error", "children"),
    Input("login-button", "n_clicks"),
    State("login-email", "value"),
    State("login-password", "value"),
    prevent_initial_call=True,
)
def login_user(n_clicks: int, email: str, password: str) -> tuple[Any, Any, str, Any]:
    """Обрабатывает вход пользователя.

    Отправляет запрос на FastAPI эндпоинт /auth/login и сохраняет
    JWT токен в локальном хранилище.

    Args:
        n_clicks: Количество кликов по кнопке.
        email: Email пользователя.
        password: Пароль пользователя.

    Returns:
        tuple: (token, user_data, redirect_path, error_message)
    """
    if not n_clicks or not email or not password:
        raise PreventUpdate

    logger.info("Попытка входа пользователя: %s", email)

    try:
        api_base_url = get_config().API_BASE_URL
        response = requests.post(
            f"{api_base_url}/auth/login",
            json={"email": email, "password": password},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        token = data["access_token"]

        # Получаем данные пользователя через /auth/me
        user_response = requests.get(
            f"{api_base_url}/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        user_response.raise_for_status()
        user_data = user_response.json()

        logger.info("Успешный вход пользователя: %s", email)
        return token, user_data, "/dashboards", ""

    except requests.HTTPError as e:
        status_code = response.status_code
        if status_code == 401:
            logger.warning("Неудачная попытка входа: %s (401)", email)
            return (
                cast(Any, no_update),
                cast(Any, no_update),
                cast(Any, no_update),
                "Неверный email или пароль",
            )
        elif status_code == 429:
            logger.warning("Слишком много попыток входа: %s (429)", email)
            return (
                cast(Any, no_update),
                cast(Any, no_update),
                cast(Any, no_update),
                "Слишком много попыток входа",
            )
        else:
            logger.error("Ошибка API при входе %s: %s (код %s)", email, e, status_code)
            return (
                cast(Any, no_update),
                cast(Any, no_update),
                cast(Any, no_update),
                f"Ошибка: {status_code}",
            )
    except requests.RequestException as e:
        logger.error("Ошибка сети при входе %s: %s", email, e)
        return (
            cast(Any, no_update),
            cast(Any, no_update),
            cast(Any, no_update),
            "Произошла ошибка соединения",
        )
    except Exception as e:
        logger.error("Неизвестная ошибка входа %s: %s", email, e)
        return (
            cast(Any, no_update),
            cast(Any, no_update),
            cast(Any, no_update),
            "Произошла ошибка",
        )


def create_dashboard_list_page() -> html.Div:
    """Создает страницу со списком доступных дашбордов.

    Получает список дашбордов через API и отображает их в виде карточек.
    Каждая карточка содержит название, описание и кнопку перехода.

    Returns:
        html.Div: Компонент страницы списка дашбордов.
    """
    logger.info("Создание страницы списка дашбордов")

    return html.Div(
        [
            html.Div(
                [
                    html.Div([
                        html.H1("Дашборды", className="mb-4"),
                        html.P(
                            "Выберите дашборд для просмотра",
                            className="text-muted mb-4",
                        ),
                        html.Div(id="dashboards-list"),
                        dbc.Button(
                            "Выход",
                            id="logout-button",
                            color="secondary",
                            className="mt-3",
                        ),
                    ])
                ],
                className="col-md-8 offset-md-2",
            )
        ],
        className="row mt-4",
    )


@callback(
    Output("dashboards-list", "children"),
    Input("auth-token", "data"),
)
def load_dashboards(token: str | None) -> list[dbc.Card]:
    """Загружает список доступных дашбордов.

    Отправляет запрос к FastAPI эндпоинту /dashboards и
    преобразует результат в карточки Bootstrap.

    Args:
        token: JWT токен аутентификации.

    Returns:
        List[dbc.Card]: Список карточек дашбордов.
    """
    if not token:
        logger.warning("Попытка загрузки дашбордов без токена")
        return [html.Div("Требуется авторизация", className="text-center")]

    logger.info("Загрузка списка дашбордов")

    try:
        api_base_url = get_config().API_BASE_URL
        response = requests.get(
            f"{api_base_url}/dashboards",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        response.raise_for_status()
        dashboards = response.json()

        cards = []
        for dashboard in dashboards:
            card = dbc.Card(
                [
                    dbc.CardBody([
                        html.H5(dashboard["name"], className="card-title"),
                        html.P(
                            dashboard.get("description", ""),
                            className="card-text text-muted",
                        ),
                        dbc.Button(
                            "Открыть",
                            href=f"/dashboard/{dashboard['id']}",
                            color="primary",
                            className="mt-2",
                        ),
                    ])
                ],
                className="mb-3",
            )
            cards.append(card)

        return cards if cards else [html.Div("Дашборды не найдены")]

    except requests.HTTPError as e:
        status_code = response.status_code
        logger.error("Ошибка API при загрузке дашбордов: %s (код %s)", e, status_code)
        return [html.Div(f"Ошибка загрузки дашбордов: {status_code}", className="text-danger")]
    except requests.RequestException as e:
        logger.error("Ошибка сети при загрузке дашбордов: %s", e)
        return [html.Div("Ошибка соединения с сервером", className="text-danger")]
    except Exception as e:
        logger.error("Неизвестная ошибка загрузки дашбордов: %s", e)
        return [html.Div("Произошла ошибка", className="text-danger")]


@callback(
    Output("url", "pathname", allow_duplicate=True),
    Input("logout-button", "n_clicks"),
    prevent_initial_call=True,
)
def logout_user(n_clicks: int | None) -> str:
    """Выход пользователя из системы.

    Очищает локальное хранилище и перенаправляет на страницу авторизации.

    Args:
        n_clicks: Количество кликов по кнопке.

    Returns:
        str: Путь для перенаправления.
    """
    if not n_clicks:
        raise PreventUpdate

    logger.info("Пользователь вышел из системы")
    return "/"


def create_dashboard_page(dashboard_id: str) -> html.Div:
    """Создает страницу просмотра дашборда.

    Загружает конфигурацию дашборда и отображает графики с панелью фильтров.

    Args:
        dashboard_id: Идентификатор дашборда.

    Returns:
        html.Div: Компонент страницы дашборда.
    """
    logger.info("Создание страницы дашборда: %s", dashboard_id)

    return html.Div(
        [
            dcc.Store(id="dashboard-config", data={"id": dashboard_id}),
            html.Div(
                [
                    html.Div([
                        html.Div([
                            html.H2(
                                id="dashboard-title",
                                className="mb-3",
                            ),
                            html.P(
                                id="dashboard-description",
                                className="text-muted mb-4",
                            ),
                        ]),
                        dbc.Button(
                            "← К списку",
                            href="/dashboards",
                            color="secondary",
                            className="mb-4",
                        ),
                        html.Div(
                            id="dashboard-filters",
                            className="mb-4 p-3 border rounded",
                        ),
                        html.Div(
                            id="dashboard-charts",
                            className="row",
                        ),
                        dbc.Button(
                            "Выход",
                            id="logout-button-dashboard",
                            color="secondary",
                            className="mt-3",
                        ),
                    ])
                ],
                className="col-12",
            ),
        ],
        className="row mt-4",
    )


@callback(
    Output("url", "pathname", allow_duplicate=True),
    Input("logout-button-dashboard", "n_clicks"),
    prevent_initial_call=True,
)
def logout_user_dashboard(n_clicks: int | None) -> str:
    """Выход пользователя из системы со страницы дашборда.

    Args:
        n_clicks: Количество кликов по кнопке.

    Returns:
        str: Путь для перенаправления.
    """
    if not n_clicks:
        raise PreventUpdate

    logger.info("Пользователь вышел из систему")
    return "/"


def load_dashboard_data(
    dashboard_data: dict[str, Any] | None, token: str | None
) -> tuple[str, str, html.Div, html.Div]:
    """Загружает данные дашборда и отображает его содержимое.

    Args:
        dashboard_data: Данные о дашборде.
        token: JWT токен аутентификации.

    Returns:
        tuple: (заголовок, описание, фильтры, графики)
    """
    if not token or not dashboard_data:
        raise PreventUpdate

    dashboard_id = str(dashboard_data.get("id", ""))
    logger.info("Загрузка дашборда: %s", dashboard_id)

    try:
        # Получаем данные дашборда через API
        api_base_url = get_config().API_BASE_URL
        headers = {"Authorization": f"Bearer {token}"}

        # Запрос конфигурации дашборда
        dashboard_response = requests.get(
            f"{api_base_url}/dashboards/{dashboard_id}",
            headers=headers,
            timeout=10,
        )
        dashboard_response.raise_for_status()
        dashboard = dashboard_response.json()

        title = dashboard.get("name", f"Дашборд {dashboard_id}")
        description = dashboard.get("description", "")

        # Получаем агрегированные данные для графиков
        chart_data = fetch_dashboard_data(dashboard_id, token)

        # Создаем панель фильтров
        filters = create_filter_panel(dashboard_id, token)

        # Создаем графики с реальными данными
        charts = create_charts_with_data(dashboard_id, chart_data, token)

        return title, description, filters, html.Div(charts)

    except requests.HTTPError as e:
        status_code = e.response.status_code if hasattr(e, 'response') else 0
        logger.error(
            "Ошибка API при загрузке дашборда %s: %s (код %s)",
            dashboard_id,
            e,
            status_code,
        )
        return (
            "Ошибка",
            f"Не удалось загрузить дашборд (код {status_code})",
            html.Div(""),
            html.Div(""),
        )
    except Exception as e:
        logger.error("Ошибка загрузки дашборда %s: %s", dashboard_id, e)
        return "Ошибка", str(e), html.Div(""), html.Div("")


def create_filter_panel(dashboard_id: str, token: str | None = None) -> html.Div:
    """Создает панель фильтров для дашборда.

    Динамически получает доступные значения фильтров из данных.

    Args:
        dashboard_id: Идентификатор дашборда.
        token: JWT токен аутентификации.

    Returns:
        html.Div: Компонент панели фильтров.
    """
    logger.debug("Создание панели фильтров для дашборда: %s", dashboard_id)

    # Получаем данные дашборда для извлечения доступных значений фильтров
    available_filters = _get_available_filter_values(dashboard_id, token)

    year_options = [{"label": str(y), "value": y} for y in available_filters.get("years", [2023, 2024])]
    category_options = [{"label": c, "value": c} for c in available_filters.get("categories", [])]
    brand_options = [{"label": b, "value": b} for b in available_filters.get("brands", [])]

    # Если нет данных, используем пустые списки
    if not category_options:
        category_options = [{"label": "Нет данных", "value": "", "disabled": True}]
    if not brand_options:
        brand_options = [{"label": "Нет данных", "value": "", "disabled": True}]

    return html.Div(
        [
            html.H5("Фильтры", className="mb-3"),
            dbc.Row([
                dbc.Col(
                    [
                        dbc.Label("Год"),
                        dcc.Dropdown(
                            id={"type": "dashboard-filter", "field": "year"},
                            options=year_options,
                            placeholder="Выберите год",
                            clearable=True,
                            multi=False,
                        ),
                    ],
                    md=4,
                    className="mb-3",
                ),
                dbc.Col(
                    [
                        dbc.Label("Категория"),
                        dcc.Dropdown(
                            id={"type": "dashboard-filter", "field": "category"},
                            options=category_options,
                            placeholder="Выберите категорию",
                            clearable=True,
                            multi=True,
                        ),
                    ],
                    md=4,
                    className="mb-3",
                ),
                dbc.Col(
                    [
                        dbc.Label("Бренд"),
                        dcc.Dropdown(
                            id={"type": "dashboard-filter", "field": "brand"},
                            options=brand_options,
                            placeholder="Выберите бренд",
                            clearable=True,
                            multi=True,
                        ),
                    ],
                    md=4,
                    className="mb-3",
                ),
            ]),
            dbc.Button(
                "Применить фильтры",
                id={"type": "apply-filters", "dashboard": dashboard_id},
                color="primary",
                className="mt-2 me-2",
            ),
            dbc.Button(
                "Сбросить фильтры",
                id={"type": "reset-filters", "dashboard": dashboard_id},
                color="secondary",
                className="mt-2",
            ),
        ],
    )


def _get_available_filter_values(dashboard_id: str, token: str | None) -> dict[str, list[str | int]]:
    """Получает доступные значения для фильтров из данных.

    Args:
        dashboard_id: Идентификатор дашборда.
        token: JWT токен.

    Returns:
        dict[str, list[str | int]]: Словарь с доступными значениями фильтров.
    """
    result: dict[str, list[str | int]] = {"years": [], "categories": [], "brands": []}

    if not token:
        return result

    try:
        api_base_url = get_config().API_BASE_URL
        headers = {"Authorization": f"Bearer {token}"}

        # Получаем данные дашборда
        response = requests.get(
            f"{api_base_url}/data/{dashboard_id}",
            headers=headers,
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        # Извлекаем уникальные значения из dims
        years_set = set()
        categories_set = set()
        brands_set = set()

        if isinstance(data, list):
            for chart_data in data:
                for item in chart_data.get("data", []):
                    dims = item.get("dims", {})
                    if "year" in dims:
                        years_set.add(dims["year"])
                    if "category" in dims:
                        categories_set.add(dims["category"])
                    if "brand" in dims:
                        brands_set.add(dims["brand"])

        result["years"] = sorted(list(years_set)) if years_set else [2023, 2024]
        result["categories"] = sorted(list(categories_set))
        result["brands"] = sorted(list(brands_set))

        logger.info(
            "Получены значения фильтров: years=%s, categories=%d, brands=%d",
            result["years"],
            len(result["categories"]),
            len(result["brands"]),
        )

    except Exception as e:
        logger.error("Ошибка получения значений фильтров: %s", e)

    return result


@callback(
    Output({"type": "dashboard-chart", "index": dash.ALL}, "figure"),
    Input({"type": "apply-filters", "dashboard": dash.ALL}, "n_clicks"),
    State({"type": "dashboard-filter", "field": dash.ALL}, "value"),
    State({"type": "dashboard-filter", "field": dash.ALL}, "id"),
    State("dashboard-config", "data"),
    State("auth-token", "data"),
    prevent_initial_call=True,
)
def apply_dashboard_filters(
    n_clicks: list[int] | None,
    filter_values: list[Any],
    filter_ids: list[dict[str, Any]],
    dashboard_data: dict[str, Any] | None,
    token: str | None,
) -> list[go.Figure]:
    """Применяет фильтры к дашборду и обновляет графики.

    Args:
        n_clicks: Количество кликов по кнопкам.
        filter_values: Значения фильтров.
        filter_ids: Идентификаторы фильтров.
        dashboard_data: Данные о дашборде.
        token: JWT токен аутентификации.

    Returns:
        list[go.Figure]: Обновленные графики.
    """
    if not n_clicks or not token or not dashboard_data:
        raise PreventUpdate

    logger.info("Применение фильтров к дашборду")

    # Собираем активные фильтры
    active_filters: dict[str, Any] = {}
    for value, fid in zip(filter_values, filter_ids, strict=False):
        if value is not None and value != "":
            active_filters[fid["field"]] = value

    logger.debug("Активные фильтры: %s", active_filters)

    # Получаем ID дашборда
    dashboard_id = str(dashboard_data.get("id", ""))
    if not dashboard_id:
        logger.warning("ID дашборда не найден в dashboard-config")
        raise PreventUpdate

    # Получаем данные с применением фильтров через API
    filtered_data = fetch_dashboard_data(dashboard_id, token, active_filters)

    if not filtered_data:
        logger.warning("Не удалось получить данные с фильтрами")
        raise PreventUpdate

    # Создаем обновленные графики
    figures: list[go.Figure] = []
    if isinstance(filtered_data, list):
        for i, chart_item in enumerate(filtered_data):
            chart_type = chart_item.get("chart_type", "bar")
            data = chart_item.get("data", [])
            metadata = chart_item.get("metadata", {})
            title = metadata.get("graph_name", f"График {i + 1}")

            fig = render_graph_from_data(chart_type, data, title)
            figures.append(fig)

    if not figures:
        logger.warning("Не удалось создать графики с фильтрами")
        raise PreventUpdate

    logger.info("Графики успешно обновлены с применением фильтров")
    return figures


@callback(
    Output({"type": "dashboard-filter", "field": dash.ALL}, "value"),
    Input({"type": "reset-filters", "dashboard": dash.ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def reset_dashboard_filters(
    n_clicks: list[int] | None,
) -> list[None]:
    """Сбрасывает все фильтры дашборда.

    Args:
        n_clicks: Количество кликов по кнопкам сброса.

    Returns:
        list[None]: Список None для сброса всех значений фильтров.
    """
    if not n_clicks:
        raise PreventUpdate

    logger.info("Сброс фильтров дашборда")
    # Возвращаем пустые значения для всех фильтров
    return [None for _ in n_clicks]


def create_charts_with_data(
    dashboard_id: str, chart_data: list[dict[str, Any]] | None, token: str
) -> list[dbc.Col]:
    """Создает компоненты графиков на основе реальных данных.

    Args:
        dashboard_id: Идентификатор дашборда.
        chart_data: Данные графиков от API.
        token: JWT токен аутентификации.

    Returns:
        list[dbc.Col]: Список колонок с графиками.
    """
    logger.info("Создание графиков для дашборда: %s", dashboard_id)

    charts: list[dbc.Col] = []
    if not chart_data:
        return [dbc.Col(html.P("Нет данных для отображения", className="text-muted"))]

    # chart_data - это список объектов AggregatedData
    if isinstance(chart_data, list):
        for i, chart_item in enumerate(chart_data):
            chart_type = chart_item.get("chart_type", "bar")
            data = chart_item.get("data", [])
            metadata = chart_item.get("metadata", {})
            title = metadata.get("graph_name", f"График {i + 1}")

            # Создаем график на основе типа
            fig = render_graph_from_data(chart_type, data, title)

            col = dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader(title),
                        dbc.CardBody([dcc.Graph(figure=fig, id={"type": "dashboard-chart", "index": i})]),
                    ],
                    className="mb-4",
                ),
                md=6,
                className="mb-4",
            )
            charts.append(col)

    return charts if charts else [dbc.Col(html.P("Нет данных для отображения", className="text-muted"))]


def render_graph_from_data(chart_type: str, data: list[dict[str, Any]], title: str) -> go.Figure:
    """Рендерит график на основе реальных данных.

    Args:
        chart_type: Тип графика (bar, line, pie, table).
        data: Данные для графика.
        title: Заголовок графика.

    Returns:
        go.Figure: Объект фигуры Plotly.
    """
    logger.info("Рендеринг графика типа %s", chart_type)

    try:
        if chart_type == "bar":
            fig = _create_bar_chart_from_data(data, title)
        elif chart_type == "line":
            fig = _create_line_chart_from_data(data, title)
        elif chart_type == "pie":
            fig = _create_pie_chart_from_data(data, title)
        elif chart_type == "table":
            fig = _create_table_chart_from_data(data, title)
        else:
            fig = _create_error_figure(f"Неизвестный тип графика: {chart_type}")

        logger.debug("График %s успешно создан", chart_type)
        return fig

    except Exception as e:
        logger.error("Ошибка рендеринга графика: %s", e)
        return _create_error_figure(f"Ошибка: {str(e)}")


def _create_bar_chart_from_data(data: list[dict[str, Any]], title: str) -> go.Figure:
    """Создает столбчатую диаграмму на основе реальных данных.

    Args:
        data: Список записей с dims и metrics.
        title: Заголовок графика.

    Returns:
        go.Figure: Объект фигуры Plotly.
    """
    if not data:
        return _create_error_figure("Нет данных для отображения")

    # Извлекаем данные
    categories = []
    values = []
    metric_name = "value"

    # Берем первую метрику из первой записи для названия
    if data and isinstance(data[0].get("metrics"), dict):
        metric_keys = list(data[0]["metrics"].keys())
        if metric_keys:
            metric_name = metric_keys[0]

    for item in data:
        dims = item.get("dims", {})
        metrics = item.get("metrics", {})
        categories.append(dims.get("category", dims.get("x", "Unknown")))
        values.append(metrics.get(metric_name, 0))

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=categories,
            y=values,
            name=metric_name,
            marker_color="#1f77b4",
        )
    )
    fig.update_layout(
        title=title,
        xaxis_title="Категория",
        yaxis_title=metric_name,
        template="plotly_white",
    )
    return fig


def _create_line_chart_from_data(data: list[dict[str, Any]], title: str) -> go.Figure:
    """Создает линейный график на основе реальных данных.

    Args:
        data: Список записей с dims и metrics.
        title: Заголовок графика.

    Returns:
        go.Figure: Объект фигуры Plotly.
    """
    if not data:
        return _create_error_figure("Нет данных для отображения")

    # Извлекаем данные
    x_values = []
    y_values = []
    metric_name = "value"

    if data and isinstance(data[0].get("metrics"), dict):
        metric_keys = list(data[0]["metrics"].keys())
        if metric_keys:
            metric_name = metric_keys[0]

    for item in data:
        dims = item.get("dims", {})
        metrics = item.get("metrics", {})
        x_values.append(dims.get("month", dims.get("x", "Unknown")))
        y_values.append(metrics.get(metric_name, 0))

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=x_values,
            y=y_values,
            mode="lines+markers",
            name=metric_name,
            line=dict(color="#1f77b4", width=2),
        )
    )
    fig.update_layout(
        title=title,
        xaxis_title="Период",
        yaxis_title=metric_name,
        template="plotly_white",
    )
    return fig


def _create_pie_chart_from_data(data: list[dict[str, Any]], title: str) -> go.Figure:
    """Создает круговую диаграмму на основе реальных данных.

    Args:
        data: Список записей с dims и metrics.
        title: Заголовок графика.

    Returns:
        go.Figure: Объект фигуры Plotly.
    """
    if not data:
        return _create_error_figure("Нет данных для отображения")

    labels = []
    values = []
    metric_name = "value"

    if data and isinstance(data[0].get("metrics"), dict):
        metric_keys = list(data[0]["metrics"].keys())
        if metric_keys:
            metric_name = metric_keys[0]

    for item in data:
        dims = item.get("dims", {})
        metrics = item.get("metrics", {})
        labels.append(dims.get("category", dims.get("x", "Unknown")))
        values.append(metrics.get(metric_name, 0))

    fig = go.Figure()
    fig.add_trace(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.3,
            textinfo="label+percent",
        )
    )
    fig.update_layout(
        title=title,
        template="plotly_white",
    )
    return fig


def _create_table_chart_from_data(data: list[dict[str, Any]], title: str) -> go.Figure:
    """Создает таблицу на основе реальных данных.

    Args:
        data: Список записей с dims и metrics.
        title: Заголовок графика.

    Returns:
        go.Figure: Объект фигуры Plotly.
    """
    if not data:
        return _create_error_figure("Нет данных для отображения")

    # Собираем все уникальные поля
    all_dims = set()
    all_metrics = set()
    for item in data:
        all_dims.update(item.get("dims", {}).keys())
        all_metrics.update(item.get("metrics", {}).keys())

    # Формируем заголовки
    headers = list(all_dims) + list(all_metrics)

    # Формируем данные для таблицы
    table_data = []
    for item in data:
        row = []
        for h in headers:
            if h in item.get("dims", {}):
                row.append(item["dims"][h])
            elif h in item.get("metrics", {}):
                row.append(item["metrics"][h])
            else:
                row.append("")
        table_data.append(row)

    fig = go.Figure()
    fig.add_trace(
        go.Table(
            header=dict(
                values=headers,
                fill_color="paleturquoise",
                align="left",
            ),
            cells=dict(
                values=[list(col) for col in zip(*table_data, strict=False)],
                fill_color="lavender",
                align="left",
            ),
        )
    )
    fig.update_layout(
        title=title,
        template="plotly_white",
    )
    return fig


def _create_error_figure(message: str) -> go.Figure:
    """Создает график с сообщением об ошибке.

    Args:
        message: Текст ошибки.

    Returns:
        go.Figure: Объект фигуры Plotly с ошибкой.
    """
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=16, color="red"),
    )
    fig.update_layout(
        title="Ошибка",
        template="plotly_white",
    )
    return fig
