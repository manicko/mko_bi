TASK: исправление импортов в service_interfaces.py

FILE: src/mko_bi/interfaces/service_interfaces.py

GOAL: исправить неверный импорт GraphRead

IMPLEMENT:

заменить:
from mko_bi.models.graph import GraphRead

на:
from mko_bi.models.graph import GraphRead

или если модели в db/models:
from mko_bi.db.models.graphs import GraphRead

LOGIC:

проверить существование целевого модуля
обновить все импорты GraphRead в файле
проверить наличие класса GraphRead в целевом модуле

CONSTRAINTS:

путь должен существовать
класс GraphRead должен быть определен

DONE:

импорт исправлен
файл компилируется без ошибок
тесты запускаются
