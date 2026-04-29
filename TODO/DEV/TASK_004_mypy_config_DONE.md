TASK: настройка MyPy для корректной работы

FILE: pyproject.toml

GOAL: исправить конфигурацию mypy для src-layout

IMPLEMENT:

[mypy]
python_version = "3.12"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false

[mypy.mko_bi.*]
ignore_missing_imports = true

# Для src-layout:
mypy_path = "src"
namespace_packages = false

LOGIC:

настроить mypy_path на папку src
отключить namespace_packages или настроить корректно
проверить отсутствие "source file found twice"

CONSTRAINTS:

конфигурация должна работать с src/mko_bi пакетом
не должно быть дублирования модулей

DONE:

uv run mypy src/ проходит без ошибок конфигурации
source file found twice исправлено
