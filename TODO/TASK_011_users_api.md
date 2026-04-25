TASK: API управления пользователями

FILE: src/mko_bi/api/routes/users.py

GOAL: Создать эндпоинты для CRUD операций с пользователями

IMPLEMENT:

router: APIRouter с prefix="/users"

@endpoint: GET /users
@endpoint: GET /users/{user_id}
@endpoint: PUT /users/{user_id}
@endpoint: DELETE /users/{user_id}

LOGIC:
- GET /users: список всех пользователей (admin only)
- GET /users/{id}: получить пользователя по ID
- PUT /users/{id}: обновить роль пользователя
- DELETE /users/{id}: удалить пользователя
- Все операции через UserService

CONSTRAINTS:
- Защита через Depends(get_current_user)
- Admin only для GET /users и DELETE
- Валидация через Pydantic модели
- HTTP статусы: 200, 204, 403, 404
- Пагинация для GET /users (опционально)

DONE:
- Эндпоинты созданы и защищены
- CRUD операции работают
- Проверки прав применены
- Валидация работает
- Тесты написаны