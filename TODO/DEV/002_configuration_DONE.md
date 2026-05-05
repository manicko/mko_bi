---
## BLOCK 2: CONFIGURATION & SETTINGS
---

### TASK: Pydantic Settings config

FILE: `src/mko_bi/config.py`

GOAL: Централизованная конфигурация с поддержкой множественных источников (SPEC.md п.6.1)

IMPLEMENT:

* class `Settings(BaseSettings)`:
  * `app_name: str = "mko_bi"`
  * `environment: EnvironmentEnum`
  * `debug: bool = False`
  * `host: str = "0.0.0.0"`
  * `port: int = 8000`
  * Database settings (DATABASE__*):
    * `database__host: str`
    * `database__port: int`
    * `database__user: str`
    * `database__password: str | None` (from env/Docker secret)
    * `database__database: str`
  * JWT settings (JWT__*):
    * `jwt__secret_key: str`
    * `jwt__algorithm: str = "HS256"`
    * `jwt__access_token_expire_minutes: int = 30`
  * Upload settings:
    * `max_file_size_mb: int = 100`
    * `allowed_extensions: list[str]`
    * `allowed_mime_types: list[str]`
  * CORS settings:
    * `cors__allow_origins: list[str]`
  * Logging:
    * `log_level: str = "INFO"`
    * `log_file: str | None`

LOGIC:

1. Использовать `pydantic-settings` BaseSettings
2. `model_config = SettingsConfigDict(env_file=".env", env_nested_delimiter="__")`
3. Поддержка `_FILE` суффикса для Docker secrets (чтение из файла)
4. Приоритет: env vars > Docker secrets > .env > YAML > defaults
5. Метод `load_yaml_config()` для app.yaml

DONE:

* [ ] Settings class работает
* [ ] Чтение из .env
* [ ] Чтение из Docker secrets (_FILE суффикс)
* [ ] YAML config загружается
* [ ] Тест на приоритет источников

---

### TASK: App YAML config

FILE: `src/mko_bi/settings/app.yaml`

GOAL: Нечувствительные настройки (SPEC.md п.6.1)

IMPLEMENT:

```yaml
app:
  name: mko_bi
  version: 1.0.0

upload:
  temp_dir_prefix: "mko_bi_upload"
  
email:
  blocked_domains:
    - "tempmail.com"
    - "throwaway.email"

dashboard:
  default_items_per_page: 20

logging:
  json_logging: true
```

LOGIC:

1. Только нечувствительные настройки
2. Хосты, порты, пути, домены
3. Читается через `yaml.safe_load()`

DONE:

* [ ] app.yaml создан
* [ ] Загружается через Settings
* [ ] Пример .env.example создан

---

### TASK: Database session configuration

FILE: `src/mko_bi/db/session.py`

GOAL: Async SQLAlchemy session с asyncpg

IMPLEMENT:

* `async_engine` создание с `asyncpg` драйвером
* `async_sessionmaker` настройка
* `get_db()` dependency для FastAPI
* `DatabaseStarter` класс для инициализации (lifespan)

LOGIC:

1. Использовать `create_async_engine(DATABASE_URL, echo=False)`
2. `async_sessionmaker(expire_on_commit=False)`
3. Поддержка `NullPool` для production
4. `DATABASE_URL` формируется из Settings

DONE:

* [ ] Engine создается
* [ ] Session работает в FastAPI
* [ ] DatabaseStarter инициализирует БД при старте

---
