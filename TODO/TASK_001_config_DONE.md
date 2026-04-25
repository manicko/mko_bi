TASK: Настройка конфигурации приложения и логирования

FILE: src/mko_bi/config.py
FILE: src/mko_bi/settings/app.yaml
FILE: src/mko_bi/logging_config.py

GOAL: Настроить подключение к PostgreSQL 18, параметры JWT, загрузки файлов и логирование

IMPLEMENT:

func: load_config()
func: setup_logging()

LOGIC:
- Расширить config.py: DATABASE_URL для PostgreSQL, JWT настройки, параметры файлов
- Создать logging_config.py с настройками для INFO, WARNING, ERROR уровней
- Настроить формат логов: timestamp, module, level, message
- Добавить константы для загрузки файлов: UPLOAD_TEMP_DIR, ALLOWED_FILE_TYPES, MAX_FILE_SIZE
- Настроить app.yaml для подключения к PostgreSQL 18 (host: localhost, port: 5432)

CONSTRAINTS:
- Использовать переменные окружения с fallback значениями
- PostgreSQL: dbname=mydb, user=postgres, password=1234, host=localhost, port=5432
- JWT: SECRET_KEY, ALGORITHM=HS256, ACCESS_TOKEN_EXPIRE_MINUTES=30
- Логирование: формат '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
- Загрузка файлов: только .csv.gz, максимум 100MB

DONE:
- Конфигурация PostgreSQL доступна через config.py
- Настройки JWT определены
- Логгер настроен с правильным форматом
- Параметры загрузки файлов заданы
- app.yaml содержит корректные настройки подключения