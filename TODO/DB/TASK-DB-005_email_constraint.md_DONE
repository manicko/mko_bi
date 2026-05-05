TASK: Add email length constraint to users table

FILE: alembic/versions/*.py, src/mko_bi/models/user.py

GOAL: Prevent oversized emails and ensure DB-model consistency

IMPLEMENT:

sql: ALTER TABLE users ADD CONSTRAINT users_email_length_check CHECK (length(email) <= 255);

migration: add CHECK constraint

LOGIC:

1. Create new migration to add CHECK constraint
2. Constraint: length(email) <= 255
3. Aligns with typical email length limits and model validation

CONSTRAINTS:

не должен ломать существующие данные (проверить длину текущих email)
идемпотентная операция (IF NOT EXISTS для constraint)
235 символов - стандартный лимит email (RFC 5321)

DONE:

 constraint users_email_length_check существует
 попытка вставить email > 255 символов вызывает ошибку
 тест: проверка ограничения на уровне БД
