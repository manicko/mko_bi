TASK: структурированное логирование (JSON)

FILE: src/mko_bi/core/logging_config.py

GOAL: логи в формате JSON для production

IMPLEMENT:

import json
import logging

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "service": "mko_bi",
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)

def setup_logging():
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    logger = logging.getLogger("mko_bi")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

LOGIC:

настроить JSON форматтер для логов
добавить обязательные поля (timestamp, level, service)
настроить вывод в stdout для Docker

CONSTRAINTS:

JSON формат для production
все логи структурированы

DONE:

логи в формате JSON
все обязательные поля присутствуют
работает в Docker
