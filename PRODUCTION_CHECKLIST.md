# Production Checklist - mkobi BI Dashboard System

Этот документ содержит чек-лист для проверки готовности приложения к продакшену.

## Обязательные проверки перед деплоем

### 1. Безопасность (Security)

- [ ] **JWT_SECRET_KEY изменен** - используется сильный уникальный ключ (не default)
  ```bash
  # Генерация нового ключа:
  openssl rand -hex 32
  ```

- [ ] **DATABASE__PASSWORD сложный** - используется надежный пароль для БД
  - Минимум 16 символов
  - Содержит буквы, цифры и спецсимволы

- [ ] **CORS origins ограничены** - не используется `"*"` для продакшена
  ```env
  CORS_ORIGINS='["https://yourdomain.com"]'
  ```

- [ ] **DEBUG = False** - отключен режим отладки
  ```env
  DEBUG=false
  ```

- [ ] **HTTPS настроен** - используется SSL/TLS (через nginx или load balancer)
  - SSL сертификаты настроены
  - HTTP перенаправляется на HTTPS
  - HSTS заголовки настроены

### 2. Логирование (Logging)

- [ ] **Логи настроены** - не только stdout
  ```env
  LOGGING__LOG_FILE=/var/log/mkobi/app.log
  LOGGING__LEVEL=INFO
  LOGGING__JSON_LOGGING=true
  ```

- [ ] **Log rotation настроен** - ротация логов (через logrotate или docker logging)
- [ ] **Чувствительные данные не попадают в логи** - пароли, токены, секреты

### 3. База данных (Database)

- [ ] **Миграции применены**
  ```bash
  uv run alembic upgrade head
  ```

- [ ] **Backup настроен** - регулярное резервное копирование БД
- [ ] **Connection pooling настроен** - для продакшена (pgbouncer опционально)
- [ ] **Индексы созданы** - проверить наличие всех необходимых индексов

### 4. Docker и инфраструктура

- [ ] **Docker secrets используются для чувствительных данных**
  ```env
  DATABASE__PASSWORD_FILE=/run/secrets/db_password
  JWT__SECRET_KEY_FILE=/run/secrets/jwt_secret
  ```

- [ ] **Docker образ собирается успешно**
  ```bash
  docker build -t mkobi:latest .
  ```

- [ ] **docker-compose up работает**
  ```bash
  docker-compose up -d
  ```

- [ ] **Приложение доступно на порту 8000**
  ```bash
  curl http://localhost:8000/health
  ```

### 5. Rate Limiting

- [ ] **Rate limiting включен** для upload endpoints
  - Защита от DDoS атак
  - Ограничение количества запросов

### 6. Тестирование (Testing)

- [ ] **Тесты проходят**
  ```bash
  uv run pytest
  ```

- [ ] **Миграции протестированы** - применение на чистой БД
- [ ] **Rollback протестирован** - откат миграций

### 7. Nginx (если используется)

- [ ] **Nginx работает** - проксирует запросы к FastAPI
- [ ] **API проксируется** - `/api/*` → FastAPI (8000)
- [ ] **SPA раздается** - статические файлы React
- [ ] **Gzip сжатие включено** (опционально)
- [ ] **Кеширование статических файлов настроено** (опционально)

### 8. Мониторинг и алертинг

- [ ] **Health check endpoint работает**
  ```bash
  curl http://localhost:8000/health
  ```

- [ ] **Мониторинг настроен** (Prometheus/Grafana опционально)
- [ ] **Алертинг настроен** - уведомления об ошибках

### 9. Производительность

- [ ] **Database connection pool настроен**
- [ ] **Static files раздаются через nginx** (не через FastAPI в продакшене)
- [ ] **GZip middleware настроен** для сжатия ответов

### 10. Документация

- [ ] **README обновлен** - инструкции по деплою
- [ ] **.env.example актуален** - содержит все необходимые переменные
- [ ] **API документация доступна** - Swagger UI на `/docs`

## Команды для проверки

```bash
# Проверка здоровья приложения
curl http://localhost:8000/health

# Проверка CORS (должен быть ограничен в продакшене)
echo $CORS_ORIGINS

# Проверка JWT секрета (не должен быть default)
echo $JWT__SECRET_KEY

# Проверка DEBUG режима (должен быть false)
echo $DEBUG

# Запуск тестов
uv run pytest

# Проверка линтера
uv run ruff check .

# Проверка типов
uv run mypy .

# Проверка миграций
uv run alembic current
uv run alembic history
```

## Процесс деплоя

1. Обновить код: `git pull`
2. Обновить зависимости: `uv sync`
3. Применить миграции: `uv run alembic upgrade head`
4. Пересобрать Docker: `docker-compose build`
5. Перезапустить сервисы: `docker-compose up -d`
6. Проверить health check: `curl http://localhost:8000/health`
7. Проверить логи: `docker-compose logs -f app`

## Откат (Rollback)

В случае проблем:
```bash
# Откат миграций
uv run alembic downgrade -1

# Откат к предыдущей версии
git checkout <previous-commit>
docker-compose up -d --build
```

---

**Важно**: Все пункты должны быть проверены перед каждым деплоем в продакшен!
