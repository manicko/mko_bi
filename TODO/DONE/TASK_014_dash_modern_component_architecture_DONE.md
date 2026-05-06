TASK: рефакторинг компонентов Dash (modern architecture)

FILE: src/mkobi/dashboards/components/

GOAL: внедрить современную архитектуру компонентов с использованием StrEnum, Pydantic моделей и декомпозиции

IMPLEMENT:

1. Создать `src/mkobi/models/enums.py` с StrEnum:
   - ButtonVariant
   - FilterType
   - GraphType
   - ComponentSize

2. Создать `src/mkobi/models/style.py` с Pydantic моделями:
   - ComponentStyle
   - ButtonStyle
   - FilterStyle
   - ChartStyle

3. Рефакторинг filters.py:
   - заменить FilterType class на импорт из enums.py
   - декомпозировать _apply_single_filter на маленькие функции (< 20 строк)
   - добавить логирование в каждую функцию

4. Рефакторинг layout.py:
   - декомпозировать _create_filter_control на маленькие функции
   - создать отдельные функции для каждого типа контрола
   - использовать Pydantic модели для конфигурации

5. Создать `src/mkobi/dashboards/components/buttons.py`:
   - Button компонент с вариантами из ButtonVariant
   - маленькие функции создания кнопок

LOGIC:

- Enum вместо строк: FilterType.SELECT вместо "select"
- Pydantic для валидации конфигов стилей
- Каждая функция < 20 строк
- Логирование: logger.debug для рендеринга, logger.info для создания компонентов

CONSTRAINTS:

- используется dash-bootstrap-components
- пакет mkobi (1 underscore)
- чистый модульный код
- логирование через logging

DONE:

- enums.py создан с StrEnum
- style.py создан с Pydantic моделями
- filters.py рефакторен (маленькие функции)
- layout.py рефакторен
- buttons.py создан
- тесты пройдены (uv run pytest)
- ruff check пройден
- mypy пройден
