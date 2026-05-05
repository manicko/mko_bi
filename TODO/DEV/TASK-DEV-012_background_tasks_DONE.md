TASK: implement background task processing for heavy operations

FILE: src/mko_bi/services/data_service.py, src/mko_bi/core/

GOAL: Move CPU-bound processing to background tasks for better scalability

IMPLEMENT:

func: integrate task queue RQ  for data processing

LOGIC:

для загрузки группы файлов или больших файлов > 100 мб:

  
если RQ:
  - установить rq: uv add rq
  - создать фоновую задачу для _process_csv_file()
  - обновить статус обработки (started -> processing -> success/failed)
  - добавить endpoint для проверки статуса задачи
  
обновить ProcessingLog модель для хранения ID задачи (если нужно)

CONSTRAINTS:

RQ требует Redis (уже есть в проекте) - 
сохранить обратную совместимость API

DONE:

задачи обработки выполняются в фоне
статус обработки обновляется корректно
 тесты проходят

