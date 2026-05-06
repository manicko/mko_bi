---
## BLOCK 19: DEPLOYMENT
---

### TASK: CORS configuration (FastAPI)

FILE: `src/mkobi/app.py`

GOAL: Настройка CORS для React SPA (SPEC.md п.23.5, SPEC_FRONTEND.md п.2.2)

IMPLEMENT:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors__allow_origins,  # ["http://localhost:3000"] для dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

LOGIC:

1. origins берутся из Settings (env vars)
2. Для production: только разрешенные домены
3. allow_credentials=True для JWT (cookies)

DONE:

* [ ] CORS настроен
* [ ] React dev server (3000) может делать запросы к FastAPI (8000)

---

### TASK: Static files serving (FastAPI)

FILE: `src/mkobi/app.py` (или отдельный файл)

GOAL: Раздача статических файлов React build (SPEC.md п.24.2 Вариант А)

IMPLEMENT:

```python
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# После всех API роутов
app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="static")


# Или fallback to index.html
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    return FileResponse("frontend/dist/index.html")
```

LOGIC:

1. Сначала собрать React: `cd frontend && npm run build`
2. FastAPI раздает статику из `frontend/dist`
3. SPA fallback: все не-API роуты → index.html

DONE:

* [ ] Статика раздается
* [ ] SPA роутинг работает

---

### TASK: Docker setup

FILE: `Dockerfile`, `docker-compose.yml`

GOAL: Docker конфигурация (SPEC.md п.24)

IMPLEMENT:

`Dockerfile`:
```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen

COPY . .

RUN uv run python -m src.mkobi.main

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "src.mkobi.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

`docker-compose.yml`:
```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_DB: bidb
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${DATABASE__PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
  
  app:
    build: .
    depends_on:
      - db
    environment:
      DATABASE__HOST: db
      DATABASE__PORT: 5432
      # ... другие переменные из .env
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data

volumes:
  postgres_data:
```

LOGIC:

1. Multi-stage build (опционально)
2. Использование uv для зависимостей
3. Docker secrets через _FILE суффикс

DONE:

* [ ] Docker image собирается
* [ ] docker-compose up работает
* [ ] Приложение доступно на порту 8000

---

### TASK: Nginx configuration

FILE: `nginx/nginx.conf`

GOAL: Nginx как reverse proxy (SPEC.md п.24.2 Вариант Б)

IMPLEMENT:

```nginx
server {
    listen 80;
    server_name localhost;

    # API requests → FastAPI
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Static files → React build
    location / {
        root /var/www/html;  # React build
        try_files $uri $uri/ /index.html;
    }
}
```

LOGIC:

1. `/api/*` проксируется на FastAPI (8000)
2. `/*` отдает статику React SPA
3. SPA fallback (try_files)

DONE:

* [ ] Nginx работает
* [ ] API проксируется
* [ ] SPA раздается

---

### TASK: Environment configs

FILE: `.env.example`, `app.yaml`

GOAL: Примеры конфигурации

IMPLEMENT:

`.env.example`:
```bash
# Database
DATABASE__HOST=localhost
DATABASE__PORT=5432
DATABASE__USER=postgres
DATABASE__PASSWORD=1234
DATABASE__DATABASE=bidb

# JWT
JWT__SECRET_KEY=your-secret-key-here
JWT__ALGORITHM=HS256

# App
ENVIRONMENT=development
LOG_LEVEL=INFO
CORS__ALLOW_ORIGINS=["http://localhost:3000"]
```

LOGIC:

1. Пример для development
2. Production настройки в Docker secrets или env vars

DONE:

* [ ] .env.example создан
* [ ] Задокументированы все переменные

---

### TASK: Production checks

FILE: (документация или checklist)

GOAL: Чек-лист для продакшена (SPEC.md п.24)

IMPLEMENT:

Production checklist:
1. [ ] JWT_SECRET_KEY изменен (не default)
2. [ ] DATABASE__PASSWORD сложный
3. [ ] CORS origins ограничены (не "*")
4. [ ] DEBUG = False
5. [ ] Логи настроены (не stdout только)
6. [ ] HTTPS настроен (nginx или load balancer)
7. [ ] Rate limiting включен
8. [ ] Docker secrets используются для чувствительных данных
9. [ ] Миграции применены (alembic upgrade head)
10. [ ] Тесты проходят (`uv run pytest`)

LOGIC:

1. Документировать процесс деплоя
2. Автоматизировать проверки (опционально)

DONE:

* [ ] Checklist создан
* [ ] Все пункты проверены перед деплоем

---
