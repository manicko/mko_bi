TASK: Сервис управления пользователями

FILE: src/mko_bi/services/user_service.py

GOAL: Реализовать бизнес-логику для CRUD операций с пользователями

IMPLEMENT:

func: create_user(email: str, password: str, role: str, db: Session) -> UserRead
func: get_user_by_email(email: str) -> Optional[UserDB]
func: get_user_by_id(user_id: int) -> Optional[UserDB]
func: update_user_role(user_id: int, new_role: str) -> Optional[UserDB]
func: delete_user(user_id: int) -> bool

LOGIC:
- create_user: делегирование в auth_service или самостоятельная реализация
- get_user_by_email: поиск через UserRepository
- get_user_by_id: получение по ID
- update_user_role: валидация роли и обновление
- delete_user: удаление пользователя
- Все операции через UserRepository

CONSTRAINTS:
- Валидация роли при создании/обновлении
- Проверка существования пользователя при обновлении
- Запрет удаления администраторов (если есть другие пользователи)
- Логирование всех операций
- Обработка ошибок и исключений
- create_user принимает сессию БД (db) как параметр

DONE:
- Все CRUD операции реализованы
- Валидация ролей работает
- Логирование добавлено
- Ошибки обрабатываются корректно
- Тесты покрывают все функции

Тесты: нужны только глубоко тестирующие бизнес-логику.