TASK: замена Any на конкретные типы

FILE: src/mko_bi/interfaces/service_interfaces.py, src/mko_bi/services/data_service.py

GOAL: конкретные типы вместо Any

IMPLEMENT:

заменить:
dict[str, Any] -> конкретный TypedDict или BaseModel

пример:
class AggregatedDataDict(TypedDict):
    dimension: str
    metric: float
    year: int
    month: int

LOGIC:

найти все использования Any
создать TypedDict или Pydantic модели для конкретных структур
заменить Any на созданные типы

CONSTRAINTS:

не использовать Any без необходимости
типы должны быть точными

DONE:

Any заменен на конкретные типы
uv run mypy проходит без ошибок типизации
