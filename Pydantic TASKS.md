## AUTH MODELS

---

### TASK: модели для логина

FILE: src/mko_bi/models/auth.py

GOAL: описать вход/выход авторизации

IMPLEMENT:

* class LoginRequest(BaseModel)
* class TokenResponse(BaseModel)

INPUT:

LoginRequest:
{
"email": "[test@test.com](mailto:test@test.com)",
"password": "123"
}

OUTPUT:

TokenResponse:
{
"access_token": "...",
"token_type": "bearer"
}

LOGIC:

1. email → EmailStr
2. password → str
3. token_type по умолчанию "bearer"

CONSTRAINTS:

* валидация email
* минимальная длина пароля (>=6)

DONE:

* [ ] модели валидируют данные
* [ ] используются в API
* [ ] тест

---

## USER MODELS

---

### TASK: базовые модели пользователя

FILE: src/mko_bi/models/user.py

GOAL: разделить внутреннюю и внешнюю модель

IMPLEMENT:

* class UserCreate(BaseModel)
* class UserRead(BaseModel)
* class UserDB(BaseModel)

LOGIC:

UserCreate:

* email
* password
* role

UserRead:

* id
* email
* role

UserDB:

* id
* email
* password_hash
* role

CONSTRAINTS:

* password не должен попадать в UserRead
* role → Literal["admin", "editor", "viewer"]

DONE:

* [ ] модели разделены
* [ ] password не утечёт
* [ ] тест

---

## DASHBOARD MODELS

---

### TASK: модели дашборда

FILE: src/mko_bi/models/dashboard.py

GOAL: описать config-driven дашборд

IMPLEMENT:

* class DashboardCreate(BaseModel)
* class DashboardRead(BaseModel)

INPUT:

{
"name": "Sales Dashboard",
"config": {...}
}

LOGIC:

1. config → dict (или Typed schema)
2. id только в Read

CONSTRAINTS:

* config обязателен
* валидировать структуру (минимум: charts list)

DONE:

* [ ] модель валидирует config
* [ ] тест

---

### TASK: схема config дашборда

FILE: src/mko_bi/models/dashboard.py

GOAL: строгая структура графиков

IMPLEMENT:

* class ChartConfig(BaseModel)
* class DashboardConfig(BaseModel)

ChartConfig:

* type: Literal["bar", "line", "pie", "table"]
* x: str
* y: str | list[str]

DashboardConfig:

* charts: list[ChartConfig]
* filters: list[str]

LOGIC:

1. валидировать тип графика
2. проверять обязательные поля

DONE:

* [ ] config валидируется
* [ ] ошибка при неверном типе графика

---

## DATA MODELS

---

### TASK: модель загрузки файла

FILE: src/mko_bi/models/data.py

GOAL: описание upload

IMPLEMENT:

* class UploadResponse(BaseModel)

OUTPUT:

{
"status": "ok"
}

DONE:

* [ ] используется в upload endpoint

---

### TASK: модель фильтров

FILE: src/mko_bi/models/data.py

GOAL: фильтрация данных

IMPLEMENT:

* class DataFilter(BaseModel)

FIELDS:

* year: int | None
* category: str | None
* brand: str | None

LOGIC:

1. все поля optional
2. используются в query params

DONE:

* [ ] фильтры валидируются
* [ ] используются в API

---

### TASK: модель ответа агрегатов

FILE: src/mko_bi/models/data.py

GOAL: унифицированный ответ API

IMPLEMENT:

* class DataResponse(BaseModel)

OUTPUT:

{
"data": [...]
}

LOGIC:

1. data → list[dict]

CONSTRAINTS:

* не жёстко типизировать (гибкость)

DONE:

* [ ] возвращает данные
* [ ] тест

---

## ACCESS MODELS

---

### TASK: модель доступа

FILE: src/mko_bi/models/user.py

GOAL: связка user-dashboard

IMPLEMENT:

* class AccessGrant(BaseModel)

FIELDS:

* user_id: int
* dashboard_id: int

DONE:

* [ ] используется в сервисах

---

## VALIDATION HELPERS

---

### TASK: кастомные валидаторы

FILE: src/mko_bi/models/dashboard.py

GOAL: сложная валидация config

IMPLEMENT:

* @validator / field_validator

LOGIC:

1. проверка что y существует
2. проверка filters допустимы

DONE:

* [ ] ошибки читаемые
* [ ] тест

---

## INTEGRATION

---

### TASK: подключить модели в API

FILE: src/mko_bi/api/routes/*

GOAL: использовать Pydantic в endpoints

IMPLEMENT:

1. request → BaseModel
2. response_model → BaseModel

DONE:

* [ ] все endpoints типизированы
* [ ] автодокументация работает

---

## SERIALIZATION

---

### TASK: orm mode / from_attributes

FILE: src/mko_bi/models/*

GOAL: совместимость с ORM

IMPLEMENT:

* model_config = ConfigDict(from_attributes=True)

DONE:

* [ ] модели работают с ORM объектами

