TASK: разрыв tight coupling в deps.py

FILE: src/mko_bi/api/deps.py

GOAL: использовать только интерфейсы в type hints

IMPLEMENT:

было:
from mko_bi.interfaces import IUserRepository, AuthService
from mko_bi.db.repositories import UserRepository
from mko_bi.services import AuthService

стало:
from mko_bi.interfaces import IUserRepository, IAuthService
from mko_bi.interfaces.repository_interfaces import IUserRepository
from mko_bi.interfaces.service_interfaces import IAuthService

def get_user_repository() -> IUserRepository:
    return UserRepository()

LOGIC:

убрать импорты конкретных реализаций (UserRepository, AuthService)
оставить только интерфейсы в type hints
инстанцировать реализации внутри фабричных методов

CONSTRAINTS:

type hints используют только интерфейсы
реализации создаются внутри функций

DONE:

deps.py использует только интерфейсы
нет прямых импортов реализаций
