TASK: Добавление аутентификации в Dash

FILE: src/mko_bi/dash_app.py

GOAL: Проверка JWT токенов в Dash приложении для ограничения доступа

IMPLEMENT:

func: middleware для проверки JWT в Dash

LOGIC:

1. В dash_app.py создать функцию проверки токена через реальную подпись:
```
from mko_bi.core.security import decode_token  # использовать существующую

def validate_jwt_token(token: str) -> dict | None:
    """Проверяет JWT токен с валидацией подписи."""
    try:
        payload = decode_token(token)
        return payload
    except Exception:
        return None
```

2. Обновить список дашбордов и страницы просмотра для проверки токена:
   - Проверять наличие токена в cookies или query параметрах
   - При отсутствии/недействительности - редирект на /dashboards/login

3. В create_login_page добавить реальную аутентификацию через FastAPI API

4. Сохранять токен в cookies после успешного логина

CONSTRAINTS:

- Использовать существующую логику JWT из core/security.py
- Токен должен передаваться через HTTP-only cookies для безопасности
- Сохранить функцию check_token_validity() для клиентской проверки

DONE:

- JWT токен проверяется при доступе к дашбордам
- Недействительный токен вызывает редирект на логин
- После логина токен сохраняется в cookies
- `uv run ruff check .` проходит

TEST:

# Запустить приложение и проверить:
# 1. Неавторизованный доступ -> редирект на логин
# 2. После логина -> доступ к списку дашбордов
uv run uvicorn mko_bi.main:app --reload
