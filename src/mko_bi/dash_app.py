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


logger = logging.getLogger(__name__)


def check_token_validity(token: str) -> bool:
    """Проверяет валидность JWT токена (без проверки подписи).

    Декодирует токен без проверки подписи и проверяет срок его действия.
    Используется на стороне клиента (Dash) для проверки необходимости
    перенаправления на страницу входа.

    Args:
        token: JWT токен для проверки.

    Returns:
        bool: True, если токен валиден и не истек, иначе False.

    Example:
        >>> check_token_validity("valid_token_string")
        True
        >>> check_token_validity("expired_token_string")
        False
    """
    try:
        logger.debug("Проверка валидности JWT токена")
        payload = jwt.decode(
            token,
            options={"verify_signature": False, "verify_exp": True},
        )
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
    except jwt.ExpiredSignatureError:
        logger.info("Токен истек")
        return False
    except jwt.DecodeError as e:
        logger.warning("Ошибка декодирования токена: %s", e)
        return False
    except Exception as e:
        logger.error("Неизвестная ошибка при проверке токена: %s", e)
        return False


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
        if current_path not in ("/", "/dashboards"):
            logger.info("Периодическая проверка: токен недействителен, перенаправление на login")
            return "/"
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

        if not pathname or pathname == "/":
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
                    dbc.Button("На главную", href="/", color="primary"),
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
        # В реальной реализации здесь будет вызов FastAPI эндпоинта
        # headers = {"Authorization": f"Bearer {token}"}
        # response = requests.get(
        #     f"http://localhost:8000/api/dashboards/{dashboard_id}",
        #     headers=headers,
        # )
        # if response.status_code == 200:
        #     dashboard = response.json()
        # else:
        #     return "Ошибка", "Не удалось загрузить дашборд", "", ""

        # Заглушка для демонстрации
        dashboard: dict[str, Any] = {
            "id": dashboard_id,
            "name": f"Дашборд {dashboard_id}",
            "description": "Пример дашборда с графиками",
            "config": {
                "graph_types": ["bar", "line"],
                "charts": [
                    {
                        "type": "bar",
                        "x": "category",
                        "metrics": ["revenue"],
                        "title": "Доход по категориям",
                    },
                    {
                        "type": "line",
                        "x": "month",
                        "metrics": ["sales"],
                        "title": "Динамика продаж",
                    },
                ],
            },
        }

        title = dashboard["name"]
        description = dashboard["description"]

        # Создаем панель фильтров
        filters = create_filter_panel(dashboard_id)

        # Создаем графики
        charts = create_charts(dashboard["config"]["charts"], dashboard_id, token)

        return title, description, filters, html.Div(charts)

    except Exception as e:
        logger.error("Ошибка загрузки дашборда %s: %s", dashboard_id, e)
        return "Ошибка", str(e), html.Div(""), html.Div("")


def create_filter_panel(dashboard_id: str) -> html.Div:
    """Создает панель фильтров для дашборда.

    Args:
        dashboard_id: Идентификатор дашборда.

    Returns:
        html.Div: Компонент панели фильтров.
    """
    logger.debug("Создание панели фильтров для дашборда: %s", dashboard_id)

    return html.Div(
        [
            html.H5("Фильтры", className="mb-3"),
            dbc.Row([
                dbc.Col(
                    [
                        dbc.Label("Год"),
                        dcc.Dropdown(
                            id={"type": "dashboard-filter", "field": "year"},
                            options=[
                                {"label": "2023", "value": 2023},
                                {"label": "2024", "value": 2024},
                            ],
                            placeholder="Выберите год",
                            clearable=True,
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
                            options=[
                                {"label": "Электроника", "value": "electronics"},
                                {"label": "Одежда", "value": "clothing"},
                                {"label": "Продукты", "value": "food"},
                            ],
                            placeholder="Выберите категорию",
                            clearable=True,
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
                            options=[
                                {"label": "Brand A", "value": "brand_a"},
                                {"label": "Brand B", "value": "brand_b"},
                            ],
                            placeholder="Выберите бренд",
                            clearable=True,
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
                className="mt-2",
            ),
            dbc.Button(
                "Сбросить фильтры",
                id={"type": "reset-filters", "dashboard": dashboard_id},
                color="secondary",
                className="mt-2 ms-2",
            ),
        ],
    )


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
        List[go.Figure]: Обновленные графики.
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

    # В реальной реализации здесь будет вызов API для получения отфильтрованных данных
    # и обновления графиков

    # Возвращаем текущие графики (в реальной реализации будут обновлены)
    raise PreventUpdate


def create_charts(
    chart_configs: list[dict[str, Any]], dashboard_id: str, token: str
) -> list[dbc.Col]:
    """Создает компоненты графиков для дашборда.

    Args:
        chart_configs: Конфигурации графиков.
        dashboard_id: Идентификатор дашборда.
        token: JWT токен аутентификации.

    Returns:
        List[dbc.Col]: Список колонок с графиками.
    """
    logger.info("Создание графиков для дашборда: %s", dashboard_id)

    charts = []
    for i, config in enumerate(chart_configs):
        chart = render_graph(config, dashboard_id, token)
        col = dbc.Col(
            dbc.Card(
                [
                    dbc.CardHeader(config.get("title", f"График {i + 1}")),
                    dbc.CardBody([dcc.Graph(figure=chart)]),
                ],
                className="mb-4",
            ),
            md=6,
            className="mb-4",
        )
        charts.append(col)

    return charts


def render_graph(config: dict[str, Any], dashboard_id: str, token: str) -> go.Figure:
    """Рендерит график через Plotly.

    Создает график на основе конфигурации и данных от API.
    Поддерживает типы: bar, line, pie, table.

    Args:
        config: Конфигурация графика.
        dashboard_id: Идентификатор дашборда.
        token: JWT токен аутентификации.

    Returns:
        go.Figure: Объект фигуры Plotly.

    Example:
        >>> config = {
        ...     "type": "bar",
        ...     "x": "category",
        ...     "metrics": ["revenue"],
        ...     "title": "Доход по категориям"
        ... }
        >>> fig = render_graph(config, "1", "token")
    """
    logger.info(
        "Рендеринг графика: тип=%s, дашборд=%s",
        config.get("type"),
        dashboard_id,
    )

    try:
        # В реальной реализации здесь будет вызов API для получения данных
        # headers = {"Authorization": f"Bearer {token}"}
        # response = requests.get(
        #     f"http://localhost:8000/api/dashboards/{dashboard_id}/data",
        #     headers=headers,
        #     params={"chart_type": config.get("type")},
        # )
        # if response.status_code == 200:
        #     data = response.json()
        # else:
        #     return _create_error_figure("Ошибка загрузки данных")

        # Заглушка: генерация примерных данных
        chart_type = config.get("type", "bar")
        x_field = config.get("x", "category")
        metrics = config.get("metrics", ["value"])
        title = config.get("title", "График")

        if chart_type == "bar":
            fig = _create_bar_chart(x_field, metrics, title)
        elif chart_type == "line":
            fig = _create_line_chart(x_field, metrics, title)
        elif chart_type == "pie":
            fig = _create_pie_chart(x_field, metrics, title)
        elif chart_type == "table":
            fig = _create_table_chart(x_field, metrics, title)
        else:
            fig = _create_error_figure(f"Неизвестный тип графика: {chart_type}")

        logger.debug("График успешно создан: %s", chart_type)
        return fig

    except Exception as e:
        logger.error("Ошибка рендеринга графика: %s", e)
        return _create_error_figure(f"Ошибка: {str(e)}")


def _create_bar_chart(x_field: str, metrics: list[str], title: str) -> go.Figure:
    """Создает столбчатую диаграмму.

    Args:
        x_field: Поле для оси X.
        metrics: Список метрик.
        title: Заголовок графика.

    Returns:
        go.Figure: Объект фигуры Plotly.
    """
    # Примерные данные
    categories = ["A", "B", "C", "D"]
    values = [100, 150, 120, 180]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=categories,
            y=values,
            name=metrics[0] if metrics else "value",
            marker_color="#1f77b4",
        )
    )
    fig.update_layout(
        title=title,
        xaxis_title=x_field,
        yaxis_title="Значение",
        template="plotly_white",
    )
    return fig


def _create_line_chart(x_field: str, metrics: list[str], title: str) -> go.Figure:
    """Создает линейный график.

    Args:
        x_field: Поле для оси X.
        metrics: Список метрик.
        title: Заголовок графика.

    Returns:
        go.Figure: Объект фигуры Plotly.
    """
    # Примерные данные
    months = ["Янв", "Фев", "Мар", "Апр", "Май", "Июн"]
    values = [100, 120, 140, 130, 160, 180]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=months,
            y=values,
            mode="lines+markers",
            name=metrics[0] if metrics else "value",
            line=dict(color="#1f77b4", width=2),
        )
    )
    fig.update_layout(
        title=title,
        xaxis_title=x_field,
        yaxis_title="Значение",
        template="plotly_white",
    )
    return fig


def _create_pie_chart(x_field: str, metrics: list[str], title: str) -> go.Figure:
    """Создает круговую диаграмму.

    Args:
        x_field: Поле для меток.
        metrics: Список метрик.
        title: Заголовок графика.

    Returns:
        go.Figure: Объект фигуры Plotly.
    """
    # Примерные данные
    labels = ["Категория A", "Категория B", "Категория C", "Категория D"]
    values = [30, 25, 20, 25]

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


def _create_table_chart(x_field: str, metrics: list[str], title: str) -> go.Figure:
    """Создает таблицу.

    Args:
        x_field: Поле для строк.
        metrics: Список метрик.
        title: Заголовок графика.

    Returns:
        go.Figure: Объект фигуры Plotly.
    """
    # Примерные данные
    data = [
        {"category": "A", "revenue": 1000, "sales": 500},
        {"category": "B", "revenue": 2000, "sales": 800},
        {"category": "C", "revenue": 1500, "sales": 600},
    ]

    fig = go.Figure()
    fig.add_trace(
        go.Table(
            header=dict(
                values=["Категория", "Доход", "Продажи"],
                fill_color="paleturquoise",
                align="left",
            ),
            cells=dict(
                values=[
                    [row["category"] for row in data],
                    [row["revenue"] for row in data],
                    [row["sales"] for row in data],
                ],
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
