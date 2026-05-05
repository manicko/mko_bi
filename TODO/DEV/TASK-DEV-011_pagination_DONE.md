TASK: Add pagination to aggregated data endpoints

FILE: src/mko_bi/api/routes/data.py, src/mko_bi/services/data_service.py

GOAL: Handle large datasets efficiently with limit/offset

IMPLEMENT:

func: add pagination parameters to data endpoints

LOGIC:

в data.py API route добавить query параметры:
  - limit: int = Query(default=100, ge=1, le=1000)
  - offset: int = Query(default=0, ge=0)
  
в data_service.py методе получения агрегированных данных:
  - добавить параметры limit и offset
  - передать их в repository метод
  
в aggregated_data_repo.py:
  - добавить limit и offset в query
  - использовать .limit(limit).offset(offset)
  
вернуть метаданные пагинации в ответе:
  {
    "data": [...],
    "pagination": {"total": 1234, "limit": 100, "offset": 0}
  }

CONSTRAINTS:

дефолтный limit не более 1000 записей
offset должен быть >= 0
сохранить обратную совместимость (старые клиенты работают без пагинации)

DONE:

 пагинация добавлена к endpoints агрегированных данных
 метаданные пагинации возвращаются в ответе
 тесты на пагинацию добавлены
