TASK: обработка ошибок в Dash callbacks

FILE: src/mko_bi/dash_app.py

GOAL: корректная обработка ошибок на фронтенде

IMPLEMENT:

@app.callback(
    Output("output", "children"),
    Input("submit", "n_clicks"),
    prevent_initial_call=True
)
def login_user(n_clicks):
    try:
        response = requests.post(f"{API_URL}/login", ...)
        response.raise_for_status()
        return "Success"
    except requests.HTTPError as e:
        if response.status_code == 401:
            return "Неверный email или пароль"
        elif response.status_code == 429:
            return "Слишком много попыток входа"
        else:
            return f"Ошибка: {response.status_code}"
    except Exception as e:
        logger.error("Login error: %s", e)
        return "Произошла ошибка"

LOGIC:

добавить обработку различных статус-кодов ответов
показывать пользователю понятные сообщения
логировать ошибки API вызовов

CONSTRAINTS:

понятные сообщения для пользователя
логирование ошибок

DONE:

ошибки обрабатываются корректно
пользователь видит понятные сообщения
