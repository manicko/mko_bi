TASK: Fix UUID logging format in upload.py

FILE: src/mko_bi/api/routes/upload.py

GOAL: Correct log output for UUID objects

IMPLEMENT:

func: change %d to %s for UUID formatting

LOGIC:

найти строки с логированием где dashboard_id форматируется через %d
заменить %d на %s для UUID объектов (lines 75-76)
Пример:
  # Было:
  logger.info("Uploading file for dashboard_id=%d", dashboard_id)
  # Стало:
  logger.info("Uploading file for dashboard_id=%s", dashboard_id)

проверить другие места в коде где UUID форматируется через %d

CONSTRAINTS:

использовать %s для UUID, строк и других нечисловых типов
%d использовать только для целых чисел (int)
не менять логику обработки

DONE:

 все UUID объекты логируются через %s
 формат вывода логов корректный
 тесты проходят
