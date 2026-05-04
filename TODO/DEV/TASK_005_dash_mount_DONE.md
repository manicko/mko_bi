TASK: Подключение Dash к FastAPI через mount

FILE: src/mko_bi/app.py
FILE: src/mko_bi/dash_app.py

GOAL: Интеграция Dash приложения в FastAPI для работы по единому порту

IMPLEMENT:

func: монтирование Dash как sub-application в FastAPI

LOGIC:

1. В app.py импортировать создание Dash приложения:
```
from mko_bi.dash_app import create_dash_app
```

2. В create_app() после регистрации роутеров добавить:
```
# Создание и монтирование Dash приложения
dash_app = create_dash_app()
app.mount("/dashboards", dash_app.server)
```

3. Убедиться что Dash использует тот же lifespan что и FastAPI (для БД)

4. Проверить что статические ресурсы Dash доступны по /dashboards/*

CONSTRAINTS:

- Dash должен быть доступен по пути /dashboards
- Использовать существующую функцию create_dash_app() из dash_app.py
- Не менять логику Dash приложения в этом таске

DONE:

- Dash приложение смонтировано к FastAPI
- Доступно по адресу http://localhost:8000/dashboards/
- Статические ресурсы отдаются корректно
- `uv run ruff check .` проходит

TEST:

uv run uvicorn mko_bi.main:app --reload
# Проверить в браузере http://localhost:8000/dashboards/
