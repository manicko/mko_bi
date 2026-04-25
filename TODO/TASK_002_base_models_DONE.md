TASK: Создание базовых моделей SQLAlchemy

FILE: src/mko_bi/db/base.py
FILE: src/mko_bi/db/models/user.py
FILE: src/mko_bi/db/models/dashboard.py
FILE: src/mko_bi/db/models/access.py

GOAL: Создать таблицы для пользователей, дашбордов и доступа в PostgreSQL

IMPLEMENT:

class: User (SQLAlchemy model)
class: Dashboard (SQLAlchemy model)
class: Access (SQLAlchemy model)
class: Base (declarative_base)
func: get_db()

LOGIC:
- Настроить engine для PostgreSQL с использованием config.DATABASE_URL
- Создать SessionLocal для управления сессиями
- Создать базовый класс Base = declarative_base()
- Модель User: id, email (unique), password_hash, role, relationships
- Модель Dashboard: id, name, config (JSON), created_at
- Модель Access: id, user_id (FK), dashboard_id (FK), permission_level
- Настроить связи: User.accesses, Dashboard.accesses
- Создать функцию get_db() как генератор сессий

CONSTRAINTS:
- Использовать SQLAlchemy ORM
- Индексы на email и уникальные ограничения
- Внешние ключи для связей
- role: String (admin/editor/viewer)
- permission_level: String (read/write/admin)
- created_at: DateTime с default=datetime.utcnow

DONE:
- Engine и SessionLocal созданы для PostgreSQL
- Модель User с правильными полями и индексами
- Модель Dashboard с конфигурацией
- Модель Access со связями
- Функция get_db() возвращает сессию