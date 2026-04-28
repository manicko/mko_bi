TASK: Создать API эндпоинты для управления фильтрами (CRUD)

FILE: src/mko_bi/api/routes/filters.py, src/mko_bi/services/filter_service.py

GOAL: Реализовать полный CRUD для глобальных фильтров с валидацией и проверкой прав доступа

IMPLEMENT:

func: create_filter()
func: get_filters()
func: get_filter()
func: update_filter()
func: delete_filter()

LOGIC:

1. В filter_service.py:
   - Слой бизнес-логики для фильтров
   - Валидация входных данных
   - Проверка прав доступа (только admin/editor)
   - Обработка ошибок
2. В api/routes/filters.py:
   - POST /filters/ - создать фильтр
   - GET /filters/ - список фильтров
   - GET /filters/{id} - получить фильтр
   - PUT /filters/{id} - обновить фильтр
   - DELETE /filters/{id} - удалить фильтр
3. Модели Pydantic:
   - FilterCreate - создание
   - FilterUpdate - обновление
   - FilterRead - чтение
   - FilterInDB - базовая

CONSTRAINTS:

- Только admin может создавать/удалять фильтры
- Editor может читать и обновлять
- Валидация config в зависимости от type
- Уникальность name
- Корректные HTTP статус-коды
- Логирование всех операций

DONE:

- CRUD API работает корректно
- Валидация данных
- Проверка прав доступа
- Swagger документация
- Тесты на все эндпоинты
- Логирование
