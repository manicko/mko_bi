TASK: Fix mypy type errors - add type arguments to dict annotations

FILE: src/mko_bi/services/dashboard_service.py, tests/test_upload_api.py, tests/test_dashboards_api.py, dashboards/components/layouts.py

GOAL: Achieve mypy clean build by fixing 15 type errors

IMPLEMENT:

func: add type arguments to all dict annotations

LOGIC:

найти все аннотации типов с dict без параметров
заменить dict на dict[str, Any] где это уместно
файлы для исправления:
  - src/mko_bi/services/dashboard_service.py (lines 353, 354, 411)
    * update_data: dict | DashboardUpdate | None = None -> dict[str, Any] | DashboardUpdate | None
    * config: dict | None = None -> dict[str, Any] | None
  - tests/test_upload_api.py (lines 17, 45, 87)
  - tests/test_dashboards_api.py (lines 16, 49, 81, 125, 159, 187, 223)
  - dashboards/components/layouts.py (line 133) - проверить возвращаемый тип

CONSTRAINTS:

использовать dict[str, Any] для аннотаций словарей
там где возвращается Any - уточнить тип или оставить Any
не менять логику кода

DONE:

 все dict аннотации имеют типизацию
 mypy проходит без ошибок (0 errors)
 тесты проходят
