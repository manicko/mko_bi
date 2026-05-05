TASK: Improve file cleanup error handling

FILE: src/mko_bi/api/routes/upload.py, src/mko_bi/services/data_service.py

GOAL: Prevent resource leaks and improve error logging

IMPLEMENT:

func: add proper logging for file cleanup operations

LOGIC:

upload.py (lines 84-90):
  - заменить pass на логирование ошибки
  - logger.error("Failed to close file: %s", e)

data_service.py (lines 633-638):
  - добавить логирование ошибок при очистке временных файлов
  - logger.error("Failed to cleanup temp file %s: %s", file_path, e)

проверить другие места где файлы закрываются или удаляются
добавить try/except с логированием где это отсутствует

CONSTRAINTS:

не подавлять исключения молча (без логирования)
логировать с подробным описанием ошибки
не прерывать основной поток выполнения из-за ошибок очистки

DONE:

 ошибки очистки файлов логируются
 ресурсные утечки предотвращены
 тесты проходят
