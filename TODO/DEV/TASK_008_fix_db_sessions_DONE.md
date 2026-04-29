TASK: исправление передачи сессий БД

FILE: src/mko_bi/services/data_service.py

GOAL: устранить множественные независимые сессии

IMPLEMENT:

передавать сессию как параметр:
def process_data(self, dashboard_id: int, session: Session = None):
    if session is None:
        with get_session() as session:
            return self._process_data_internal(dashboard_id, session)
    return self._process_data_internal(dashboard_id, session)

LOGIC:

убрать вызовы get_session() внутри методов
передавать сессию через параметры
использовать контекстный менеджер для транзакций

CONSTRAINTS:

одна транзакция на операцию
сессия передается сверху

DONE:

нет множественных сессий в одной операции
используется контекстный менеджер
