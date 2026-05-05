TASK: Add default value to users.role column

FILE: src/mko_bi/models/user.py, alembic/versions/*.py

GOAL: Ensure users.role has default value 'viewer' in DB

IMPLEMENT:

sql: ALTER TABLE users ALTER COLUMN role SET DEFAULT 'viewer'::user_role;

migration: add default to existing column

LOGIC:

1. Create new migration or modify starter
2. Add DEFAULT 'viewer'::user_role to users.role column
3. Verify ORM and DB are aligned

CONSTRAINTS:

должно соответствовать UserRoleEnum.viewer
не нарушает существующие данные
идемпотентная операция

DONE:

 users.role имеет default 'viewer'::user_role
 новый пользователь без роли получает 'viewer'
 тест: создание пользователя без указания роли
