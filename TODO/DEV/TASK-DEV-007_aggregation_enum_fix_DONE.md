TASK: Convert AggregationFunctionEnum from Enum to StrEnum

FILE: src/mko_bi/models/user_roles.py

GOAL: Ensure consistency with other enum definitions

IMPLEMENT:

func: Change class definition and update if needed

LOGIC:

изменить импорт: from enum import Enum, StrEnum -> from enum import StrEnum
изменить класс: class AggregationFunctionEnum(Enum): -> class AggregationFunctionEnum(StrEnum):
удалить метод __str__ если он был (не нужен для StrEnum)
проверить использование enum в коде (models/processing_configs.py, services/*)
убедиться что строковые значения работают корректно

CONSTRAINTS:

сохранить текущие значения (sum_val = "sum", mean = "mean", etc.)
использовать StrEnum для автоматического преобразования в строку
не менять логику использования enum

DONE:

 AggregationFunctionEnum наследуется от StrEnum
 метод __str__ удален (если был)
 все использования enum работают корректно
 тесты проходят
