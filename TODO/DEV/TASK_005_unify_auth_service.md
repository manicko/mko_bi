TASK: унификация auth_service (класс или функции)

FILE: src/mko_bi/services/auth_service.py

GOAL: выбрать один подход и придерживаться его

IMPLEMENT:

вариант (рекомендуется класс):
- оставить AuthService с методами
- переписать standalone функции register_user, login_user как методы класса
- обновить вызовы в api/routes/auth.py

LOGIC:

выбрать подход (класс AuthService)
удалить дублирующие standalone функции
обновить deps.py для использования класса
обновить роуты auth.py

CONSTRAINTS:

сохранить функциональность
не сломать существующие вызовы

DONE:

один подход (класс или функции)
нет дублирования кода
все тесты проходят
