TASK: Wrap Polars CPU-bound operations in asyncio.to_thread()

FILE: src/mko_bi/services/data_service.py

GOAL: Prevent blocking of async event loop during data processing

IMPLEMENT:

func: refactor _process_csv_file() and related functions

LOGIC:

найти все синхронные вызовы Polars (pl.read_csv, LazyFrame, collect, etc.)
обернуть их в asyncio.to_thread() для выполнения в отдельном потоке
обновить сигнатуры функций если необходимо (добавить async/await)
проверить что функция _trigger_processing_logic корректно работает с async

CONSTRAINTS:

использовать asyncio.to_thread() для CPU-bound операций
не блокировать event loop
сохранить текущую логику обработки данных

DONE:

 Polars операции выполняются в отдельном потоке
 async/await цепочка работает корректно
 тесты проходят успешно
 mypy проверка проходит
