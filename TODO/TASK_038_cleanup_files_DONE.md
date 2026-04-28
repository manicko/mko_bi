TASK: Реализовать очистку загруженных файлов после обработки

FILE: src/mko_bi/services/data_service.py, src/mko_bi/utils/file_utils.py

GOAL: Гарантировать удаление временных файлов после успешной обработки CSV для предотвращения утечки дискового пространства

IMPLEMENT:

func: cleanup_task_files()
func: _process_csv_file() - вызов cleanup после успешной обработки
func: trigger_processing() - вызов cleanup после обработки

LOGIC:

1. В _process_csv_file() после успешного сохранения агрегатов в БД:
   - Вызвать cleanup_task_files(task_id)
   - Обернуть в try/finally для гарантированного удаления
2. В trigger_processing() после завершения обработки:
   - Вызвать cleanup_task_files()
3. В cleanup_task_files():
   - Удалить все файлы в папке task_id
   - Логировать удаление
   - Обрабатывать ошибки удаления

CONSTRAINTS:

- Файлы должны удаляться даже при ошибках обработки
- Использовать try/finally для гарантии
- Логировать все операции удаления
- Не удалять файлы других задач

DONE:

- Загруженные файлы удаляются после обработки
- Нет orphaned файлов в data/tmp_uploads/
- Логирование удаления работает
- Тесты на очистку файлов
