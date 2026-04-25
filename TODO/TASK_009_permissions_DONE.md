TASK: Слой управления доступом и проверки прав

FILE: src/mko_bi/core/permissions.py
FILE: src/mko_bi/api/deps.py

GOAL: Реализовать проверку прав доступа и зависимости FastAPI

IMPLEMENT:

func: check_role(user_role: str, required_role: str) -> bool
func: check_dashboard_access(user_id: int, dashboard_id: int) -> bool
func: get_current_user(token: str) -> UserDB
func: require_role(required_role: str)

LOGIC:
- check_role: иерархия ролей (admin > editor > viewer)
- check_dashboard_access: проверка через AccessRepository
- get_current_user: декодирование JWT и получение пользователя
- require_role: dependency для FastAPI с проверкой роли
- Асинхронные зависимости для FastAPI

CONSTRAINTS:
- Использовать Depends из FastAPI
- HTTPException при отсутствии доступа
- Кэширование пользователя в request state
- Иерархия: admin может всё, editor может read/write, viewer только read
- ОбработкаExpiredSignatureError

DONE:
- Проверка ролей работает по иерархии
- Доступ к дашбордам проверяется
- JWT декодируется и валидируется
- FastAPI dependencies готовы
- Защита API через Depends реализована