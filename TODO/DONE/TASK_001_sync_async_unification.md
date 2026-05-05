TASK: Унификация sync/async кода в сервисах

FILE: src/mko_bi/services/data_service.py
FILE: src/mko_bi/api/routes/upload.py
FILE: src/mko_bi/api/deps.py

GOAL: Устранить смешение синхронного и асинхронного кода для предотвращения deadlock и race conditions

IMPLEMENT:

func: перевод всех сервисов на AsyncSession

LOGIC:

1. Заменить `from sqlalchemy.orm import Session` на `from sqlalchemy.ext.asyncio import AsyncSession` в:
   - services/data_service.py
   - api/routes/upload.py
   - всех файлах, использующих синхронную сессию

2. Обновить типизацию параметров:
   - `db: Session` -> `db: AsyncSession`

3. Заменить синхронные вызовы репозиториев на асинхронные:
   - `repo.create()` -> `await repo.create()`
   - `repo.get()` -> `await repo.get()`
   - и т.д.

4. Обновить deps.py для работы с AsyncSession:
   - `get_db()` должен возвращать асинхронную сессию

5. Проверить совместимость с существующими репозиториями
   - При необходимости добавить `async` к методам репозиториев

CONSTRAINTS:

- Все async endpoints должны использовать только AsyncSession
- Синхронный код можно выносить в `asyncio.to_thread()` если нельзя переделать
- Сохранить обратную совместимость с существующими тестами

DONE:

- Все импорты Session заменены на AsyncSession
- Синхронные вызовы репозиториев стали асинхронными
- deps.py возвращает AsyncSession
- `uv run ruff check .` проходит
- `uv run mypy src/` проходит
- `uv run pytest` проходит

TEST:

uv run pytest tests/
