TASK: Вспомогательные утилиты

FILE: src/mko_bi/utils/exceptions.py
FILE: src/mko_bi/utils/file_utils.py
FILE: src/mko_bi/utils/time_utils.py

GOAL: Создать утилиты для обработки ошибок, файлов и времени

IMPLEMENT:

class: HTTPException
class: FileUtils
class: TimeUtils

LOGIC:
- HTTPException: кастомные исключения с кодами
- FileUtils: чтение, запись, удаление, очистка временных файлов
- TimeUtils: форматирование дат, вычисление разниц

CONSTRAINTS:
- HTTPException наследовать от Exception
- FileUtils использовать pathlib
- TimeUtils использовать datetime
- Логирование ошибок
- Валидация входных параметров

DONE:
- Кастомные исключения созданы
- Утилиты для файлов работают
- Утилиты для времени работают
- Логирование ошибок добавлено
- Тесты написаны