TASK: Fix async rollback not awaited in tests

FILE: tests/test_models.py

GOAL: Eliminate RuntimeWarning for unawaited rollback

IMPLEMENT:

func: add await to async_db_session.rollback() calls

LOGIC:

найти все вызовы async_db_session.rollback() в test_models.py
добавить await перед каждым вызовом (lines 81, 178, 810)
проверить что функции в которых находятся эти вызовы являются async
убедиться что сесия async_db_session доступна в контексте

CONSTRAINTS:

использовать await async_db_session.rollback()
все async операции должны быть ожидаемы
не менять логику тестов

DONE:

 все rollback вызовы ожидаются (await)
 RuntimeWarning исчезли
 тесты проходят успешно
