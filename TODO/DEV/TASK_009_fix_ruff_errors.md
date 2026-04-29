TASK: исправление Ruff ошибок

FILE: все файлы с ошибками

GOAL: чистый код без ошибок линтера

IMPLEMENT:

1. E402 - перенести импорты в начало файла
   файл: src/mko_bi/core/permissions.py
   
2. B904 - добавить 'from' в raise
   файл: src/mko_bi/core/permissions.py:105
   raise ValueError(...) from err
   
3. UP047 - исправить generic function
   файл: src/mko_bi/utils/decorators.py:20
   def timing(func: Callable[P, T]) -> Callable[P, T]: ...
   
4. F401 - удалить неиспользуемые импорты
   файл: src/mko_bi/api/upload.py:20

LOGIC:

запустить uv run ruff check .
исправить все найденные ошибки
запустить uv run ruff check . --fix для автоисправлений

CONSTRAINTS:

все ошибки ruff исправлены
код соответствует PEP 8

DONE:

uv run ruff check . проходит без ошибок
весь код отформатирован
