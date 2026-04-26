TASK: API аутентификации

FILE: src/mko_bi/api/routes/auth.py

GOAL: Создать эндпоинты для регистрации и входа

IMPLEMENT:

router: APIRouter с prefix="/auth"

@endpoint: POST /login
@endpoint: POST /register
@endpoint: POST /refresh

LOGIC:
- POST /login: принимает email/password, возвращает JWT
- POST /register: создает пользователя, возвращает токен
- POST /refresh: обновляет истекший токен
- Все эндпоинты возвращают стандартизированные ответы
- Валидация через Pydantic модели

CONSTRAINTS:
- Использовать LoginRequest/RegisterRequest модели
- Ответы в формате JSON
- HTTP статусы: 200 OK, 401 Unauthorized, 422 Validation Error
- Защита через OAuth2PasswordBearer (для refresh)
- Rate limiting для /login (максимум 5 попыток в минуту)

DONE:
- Эндпоинт /login работает
- Эндпоинт /register создает пользователей
- Эндпоинт /refresh обновляет токены
- Валидация запросов работает
- Статусы корректны

Тесты: нужны только глубоко тестирующие бизнес-логику.