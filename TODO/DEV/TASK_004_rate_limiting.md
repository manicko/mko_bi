TASK: Добавление rate limiting для upload endpoints

FILE: src/mko_bi/api/routes/upload.py
FILE: src/mko_bi/core/security.py

GOAL: Соответствие SPEC.md п.6 — защита upload endpoints от DoS атак

IMPLEMENT:

func: применение slowapi/fastapi-limiter к upload endpoints

LOGIC:

1. Добавить fastapi-limiter в зависимости (если используется Redis для rate limiter в auth):
   - Проверить что настройки Redis для rate limiter уже есть в core/security.py

2. В upload.py добавить rate limiter:
```
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/{dashboard_id}")
@limiter.limit("10/minute")  # или другой разумный лимит
async def upload_file_endpoint(...):
    ...
```

3. Настроить сообщение об ошибке (HTTP 429 Too Many Requests)

4. Проверить что rate limiting для /auth/login продолжает работать

CONSTRAINTS:

- Использовать тот же механизм что и для /auth/login (slowapi или fastapi-limiter)
- Лимит должен быть разумным (например, 10 uploads в минуту)
- Ключом для rate limiting должен быть IP адрес или user ID

DONE:

- Upload endpoints защищены rate limiting
- При превышении лимита возвращается HTTP 429
- Существующий rate limiting для /auth/login не нарушен
- `uv run pytest tests/` проходит

TEST:

uv run pytest tests/test_upload_api.py -v
