TASK: Remove mypy ignore-errors comment and fix type issues in config.py

FILE: src/mko_bi/config.py

GOAL: Achieve proper type checking instead of ignoring errors

IMPLEMENT:

func: fix type annotations and remove ignore comment

LOGIC:

удалить строку "# mypy: ignore-errors" (line 4)
проверить типы в config.py:
  - метод __init__ параметр **data: Any - проверить
  - метод get(self, key: str, default: Any = None) -> Any - OK
  - settings_customise_sources возвращаемый тип tuple[...] - проверить
  - SecretsFileSource методы - проверить типы
запустить mypy для проверки: uv run mypy src/mko_bi/config.py
исправить найденные ошибки типизации

CONSTRAINTS:

не использовать ignore комментарии без весомой причины
исправить причины ошибок типизации
сохранить текущую логику конфигурации

DONE:

 комментарий "# mypy: ignore-errors" удален
 mypy проходит для config.py без ошибок
 тесты проходят
