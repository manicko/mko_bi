TASK: создать пользователя

FILE: src/mkobi/services/user_service.py

GOAL: создание пользователя с ролью

IMPLEMENT:

func: create_user(email, password, role)

LOGIC:

проверить уникальность email
захешировать пароль
сохранить

CONSTRAINTS:

роли: admin/editor/viewer

DONE:

 пользователь создаётся
 пароль захеширован
 тест