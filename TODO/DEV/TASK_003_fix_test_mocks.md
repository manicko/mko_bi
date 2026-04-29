TASK: исправление путей моков в тестах

FILE: tests/conftest.py

GOAL: исправить неверные пути моков

IMPLEMENT:

заменить:
patch("mko_bi.db.session.get_engine", ...)

на:
patch("mko_bi.db.session._get_engine", ...)

или экспортировать get_engine как публичную функцию

LOGIC:

найти все patch() вызовы в conftest.py
проверить реальные имена функций в mko_bi.db.session
исправить пути моков
запустить тесты

CONSTRAINTS:

имена функций должны совпадать с реальными
все моки должны работать

DONE:

все пути моков исправлены
uv run pytest проходит без ошибок импорта
