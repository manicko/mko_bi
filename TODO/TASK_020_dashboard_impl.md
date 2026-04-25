TASK: Конкретные реализации дашбордов

FILE: src/mko_bi/dashboards/implementations/dashboard_1.py
FILE: src/mko_bi/dashboards/implementations/dashboard_2.py

GOAL: Создать примеры реализации конкретных дашбордов

IMPLEMENT:

class: Dashboard1
class: Dashboard2

LOGIC:
- Dashboard1: bar chart + line chart, фильтры по году и категории
- Dashboard2: pie chart + table, фильтры по бренду
- Обе реализуют DashboardBase
- Используют компоненты графиков
- Загружают данные через API/DataService

CONSTRAINTS:
- Наследовать от DashboardBase
- Реализовать все абстрактные методы
- Использовать существующие компоненты
- Конфигурация загружается из БД
- Поддержка обновления данных

DONE:
- Dashboard1 реализован с bar и line
- Dashboard2 реализован с pie и table
- Оба дашборда работают с данными
- Фильтры применяются корректно
- Можно зарегистрировать в реестре