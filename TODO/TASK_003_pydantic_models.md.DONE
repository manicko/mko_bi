TASK: Создание Pydantic моделей для валидации

FILE: src/mko_bi/models/user.py
FILE: src/mko_bi/models/dashboard.py
FILE: src/mko_bi/models/data.py
FILE: src/mko_bi/models/auth.py

GOAL: Создать схемы Pydantic для валидации входящих и исходящих данных

IMPLEMENT:

class: UserCreate (BaseModel)
class: UserRead (BaseModel)
class: UserDB (BaseModel)
class: DashboardCreate (BaseModel)
class: DashboardRead (BaseModel)
class: DashboardConfig (BaseModel)
class: DataUpload (BaseModel)
class: ProcessingConfig (BaseModel)
class: LoginRequest (BaseModel)
class: Token (BaseModel)

LOGIC:
- UserCreate: email (EmailStr), password (str), role (Literal)
- UserRead: id, email, role (без пароля)
- UserDB: id, email, password_hash, role (для БД)
    - DashboardConfig: graph_types, filters, aggregations, charts, title, description
    - DataUpload: file, dashboard_id
    - ProcessingConfig: transformations, aggregations
    - LoginRequest: email, password
    - Token: access_token, token_type
    
    LOGIC:
    - UserCreate: email (EmailStr), password (str), role (Literal)
    - UserRead: id, email, role (без пароля)
    - UserDB: id, email, password_hash, role (для БД)
    - DashboardCreate: name, description, config (DashboardConfig)
    - DashboardRead: id, name, description, config, created_at, updated_at
    - DashboardConfig: graph_types, filters, aggregations, charts, title, description
    - DashboardUpdate: name, description, config (опционально)
    - DataUpload: file, dashboard_id
    - ProcessingConfig: transformations, aggregations
    - LoginRequest: email, password
    - Token: access_token, token_type
    - RefreshRequest: refresh_token
    
    CONSTRAINTS:
    - Использовать BaseModel из pydantic
    - EmailStr для валидации email
    - Literal для ограничения значений (роли, типы графиков)
    - Config class с from_attributes = True
    - Вложенные модели для сложных структур
    - Опциональные поля помечать как Optional

DONE:
- Все Pydantic модели созданы с правильными полями
- Валидация email работает через EmailStr
- Ограничения через Literal применены
- Вложенные модели настроены
- Config classes добавлены ко всем моделям

Тесты: нужны только глубоко тестирующие бизнес-логику.