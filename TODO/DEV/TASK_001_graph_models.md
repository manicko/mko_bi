TASK: создание Pydantic моделей для графиков

FILE: src/mko_bi/models/graph.py

GOAL: создать GraphRead, GraphCreate, GraphUpdate модели

IMPLEMENT:

class GraphBase:
    name: str
    graph_type: str
    dashboard_id: int
    config: dict[str, Any]
    order: int

class GraphCreate(GraphBase):
    pass

class GraphUpdate(BaseModel):
    name: str | None = None
    graph_type: str | None = None
    config: dict[str, Any] | None = None
    order: int | None = None

class GraphRead(GraphBase):
    id: int
    created_at: datetime
    updated_at: datetime

LOGIC:

определить поля согласно db/models/graphs.py
добавить валидацию graph_type (bar, line, pie, table)
наследовать от BaseModel

CONSTRAINTS:

совместимость с SQLAlchemy моделью Graph
использовать typing.Annotated для валидации

DONE:

модели созданы
соответствие полям БД
импорт в service_interfaces.py работает
