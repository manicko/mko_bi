"""Сервисы бизнес-логики.

Содержит реализации сервисов для работы с бизнес-логикой приложения.
Все сервисы реализуют соответствующие интерфейсы из модуля interfaces.
"""

# Импортируем только функции для обратной совместимости
# Классы-реализации импортируются напрямую из модулей

from mkobi.services.auth_service import AuthService
from mkobi.services.user_service import UserService

__all__ = [
    "AuthService",
    "UserService",
]