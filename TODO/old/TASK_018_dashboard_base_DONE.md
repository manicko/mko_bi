TASK: Dashboard base infrastructure

FILES:
- src/mko_bi/dashboards/base.py
- src/mko_bi/dashboards/registry.py

GOAL:
Создать базовый класс дашборда и реестр (factory + registry)

IMPLEMENT:

1. base.py

class: DashboardBase (ABC)

INIT:
- принимает config: DashboardConfig

ABSTRACT METHODS:

- get_data(self, filters: dict) -> list[dict]
- apply_filters(self, data: list[dict], filters: dict) -> list[dict]
- render(self, data: list[dict]) -> dict

CONSTRAINTS:
- использовать abc.ABC
- все методы строго типизированы
- не использовать глобальные зависимости

---

2. registry.py

class: DashboardRegistry

RESPONSIBILITY:
- регистрация классов дашбордов
- создание экземпляров (factory)
- кэширование

INTERNAL STRUCTURE:

- _registry: dict[str, type[DashboardBase]]
- _instances: dict[tuple[str, str], DashboardBase]

(ключ кэша = (dashboard_name, config_hash))

PUBLIC METHODS:

- register(name: str, dashboard_cls: type[DashboardBase]) -> None
- get(name: str, config: DashboardConfig) -> DashboardBase
- exists(name: str) -> bool
- clear_cache() -> None

LOGIC:

register:
- сохраняет класс
- бросает ValueError если имя уже существует

get:
- если нет в registry → KeyError
- генерирует config_hash (например через json.dumps + hash)
- если есть в _instances → вернуть
- иначе создать, закэшировать и вернуть

clear_cache:
- очищает _instances

CONSTRAINTS:

- НЕ использовать глобальный singleton instance
- использовать module-level instance:
    registry = DashboardRegistry()
- регистрация через decorator:
    @registry.register("sales")
- не создавать дашборды напрямую вне registry
- кэш должен учитывать config

ERROR HANDLING:

- KeyError если dashboard не найден
- ValueError при повторной регистрации

DONE:

- базовый класс работает
- registry регистрирует классы
- factory создаёт экземпляры
- кэширование работает корректно
