TASK: управление транзакциями

FILE: src/mko_bi/services/data_service.py, src/mko_bi/core/base_service.py

GOAL: явные commit/rollback

IMPLEMENT:

def process_uploaded_file(self, dashboard_id: int, session: Session):
    try:
        with session.begin():
            # операции с БД
            self._save_aggregated_data(session, data)
            session.commit()
    except Exception as e:
        session.rollback()
        logger.error("Transaction failed: %s", e)
        raise

LOGIC:

обернуть операции с БД в with session.begin():
добавить явный rollback при ошибках
обновить статус логов обработки при ошибках

CONSTRAINTS:

одна транзакция на операцию
rollback при любой ошибке

DONE:

транзакции управляются явно
rollback работает корректно
статусы логов обновляются
