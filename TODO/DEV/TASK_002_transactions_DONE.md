TASK: Добавление явных транзакций в data_service.py

FILE: src/mko_bi/services/data_service.py

GOAL: Обеспечить атомарность операций сохранения данных через явные транзакции

IMPLEMENT:

func: добавление async with db.begin() в критические секции

LOGIC:

1. Найти все места в data_service.py где происходит последовательная запись в БД:
   - Создание processing_log
   - Сохранение агрегированных данных
   - Обновление статусов

2. Обернуть эти операции в транзакции:
```
async with db.begin():
    processing_log = await ProcessingLogRepository.create(db, **log_create.model_dump())
    # другие операции
```

3. Убедиться что при ошибке происходит автоматический rollback

4. Для фоновых задач (BackgroundTasks) создавать новую сессию с транзакцией

CONSTRAINTS:

- Использовать только `async with db.begin():`
- Не использовать ручной rollback если не требуется специальная логика
- Транзакции должны быть максимально короткими

DONE:

- Все критические операции записи обернуты в транзакции
- При ошибке данные не сохраняются (rollback работает)
- `uv run pytest tests/` проходит

TEST:

uv run pytest tests/services/test_data_service.py -v
