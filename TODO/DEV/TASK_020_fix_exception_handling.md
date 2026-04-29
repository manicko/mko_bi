TASK: исправление обработки ошибок (замена bare except)

FILE: src/mko_bi/services/data_service.py, все файлы

GOAL: корректная обработка исключений

IMPLEMENT:

было:
try:
    ...
except:
    pass

стало:
try:
    ...
except SpecificException as e:
    logger.error("Error: %s", e)
    raise CustomException() from e

LOGIC:

найти все голые except:
заменить на конкретные исключения
добавить логирование с контекстом
использовать raise ... from e

CONSTRAINTS:

не использовать голые except:
логировать ошибки с контекстом

DONE:

нет голых except:
все ошибки обрабатываются корректно
используется raise ... from e
