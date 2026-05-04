TASK: Внедрить корректное управление секретами для production

FILE: src/mko_bi/config.py, src/mko_bi/settings/app.yaml, tests/conftest.py

GOAL: Обеспечить безопасное хранение секретов (пароли БД, JWT keys) с использованием переменных окружения и поддержкой Docker secrets

ANALYSIS:

Текущее состояние:
- `app.yaml` содержит секреты в открытом виде (DB password: "1234", JWT secret)
- `config.py` загружает YAML с приоритетом выше, чем env vars (неправильно)
- Тесты корректно используют переменные окружения через pydantic-settings

Предлагаемая архитектура (2 уровня, без overengineering):

1. **Уровень 1 - Non-sensitive config**: `app.yaml`
   - Хранит только нечувствительные настройки (хосты, порты, пути, цвета графиков)
   - Может коммититься в git
   - Пароли и секреты НЕ хранятся здесь (или имеют placeholder значения)

2. **Уровень 2 - Secrets**: Environment variables (стандарт для контейнеров)
   - `DB_PASSWORD` - пароль БД
   - `JWT__SECRET_KEY` - секретный ключ JWT
   - `REDIS__PASSWORD` - пароль Redis (опционально)
   - При запуске в контейнере переменные инжектятся через docker-compose / k8s secrets

3. **Опционально - Docker secrets file** (для production):
   - Поддержка чтения секретов из смонтированных файлов (`/run/secrets/`)
   - Формат: `DB_PASSWORD_FILE`, `JWT_SECRET_KEY_FILE`

IMPLEMENT:

1. Обновить `config.py`:
   - Исправить приоритет источников: `env vars > secrets file > YAML > defaults`
   - Добавить поддержку чтения секретов из файлов (для Docker secrets)
   - Сделать пароли обязательными (без дефолтных значений в коде)

2. Обновить `app.yaml`:
   - Убрать реальные пароли, оставить только нечувствительные настройки
   - Добавить комментарии о необходимости установки переменных окружения

3. Обновить `settings_customise_sources`:
   - Обеспечить правильный приоритет источников
   - Добавить `SecretsFileSource` для поддержки Docker secrets

4. Документация:
   - Создать `settings/README.md` с описанием того, как настраивать секреты
   - Примеры для development и production (docker-compose)

5. Обновить тесты (если нужно):
   - Тесты уже используют env vars в `conftest.py` - проверить совместимость

CONSTRAINTS:

- Использовать pydantic-settings (уже подключен)
- Без overengineering (не использовать сторонние vault решения)
- Поддержка nested env vars (pydantic-settings: `DATABASE__PASSWORD`)
- Логирование факта загрузки конфигурации (без вывода секретов)
- Pydantic models для типизации (уже есть)
- StrEnum для констант (уже есть в user_roles.py)

DONE:

- `config.py` обновлен с правильным приоритетом источников
- Секреты не попадают в git (app.yaml очищен)
- Поддержка Docker secrets работает
- Тесты проходят (`uv run pytest tests/`)
- Создан `settings/README.md` с инструкциями
- Логирование инициализации настроек (без секретов в логах)
