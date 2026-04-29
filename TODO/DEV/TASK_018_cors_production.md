TASK: настройка CORS для production

FILE: src/mko_bi/app.py, src/mko_bi/settings/app.yaml

GOAL: безопасность в production

IMPLEMENT:

# app.yaml
cors_origins:
  - "https://example.com"
  - "https://app.example.com"

# app.py
from mko_bi.config import settings

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

LOGIC:

добавить список разрешенных доменов в конфигурацию
читать origins из настроек
убрать allow_origins=["*"]

CONSTRAINTS:

конкретные домены в production
настройка через конфигурацию

DONE:

CORS настроен для production
нет wildcard в allow_origins
