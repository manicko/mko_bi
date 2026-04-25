TASK: Базовая инфраструктура дашбордов

FILE: src/mko_bi/dashboards/base.py
FILE: src/mko_bi/dashboards/registry.py

GOAL: Создать базовый класс и реестр для дашбордов

IMPLEMENT:

class: DashboardBase (абстрактный)
class: DashboardRegistry

LOGIC:
- DashboardBase: абстрактные методы render, get_data, apply_filters
- DashboardRegistry: реестр для регистрации и получения дашбордов
- Фабрика создания дашбордов по имени
- Кэширование экземпляров дашбордов

CONSTRAINTS:
- Использовать ABC для абстрактного базового класса
- Реестр как singleton
- Методы: render(), get_data(), apply_filters()
- Поддержка конфигурации через DashboardConfig
- Исключения для несуществующих дашбордов

DONE:
- DashboardBase с абстрактными методами
- DashboardRegistry работает как singleton
- Фабрика создает экземпляры
- Конфигурация передается в дашборды
- Базовая инфраструктура готова