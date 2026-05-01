TASK: интеграция Dash с реальными данными

FILE: src/mko_bi/dashboards/implementations/dashboard_1.py, dashboard_2.py

GOAL: замена заглушек на реальные API вызовы

IMPLEMENT:

class Dashboard1(BaseDashboard):
    def get_data(self, filters: dict = None):
        # было: return sample_data
        # стало:
        response = requests.get(
            f"{API_BASE_URL}/data/aggregated",
            params={"dashboard_id": self.dashboard_id},
            headers={"Authorization": f"Bearer {self.get_token()}"}
        )
        return response.json()
    
    def apply_filters(self, data, filters):
        # реальная фильтрация данных
        ...
    
    def render(self):
        data = self.get_data()
        # реальный рендеринг графиков
        ...

LOGIC:

заменить sample_data на вызовы API или сервисов
реализовать get_data(), apply_filters(), render()
подключить фильтры к бэкенду

CONSTRAINTS:

использование реальных данных
корректная обработка ошибок API

DONE:

Dash использует реальные данные
нет заглушек с sample_data
фильтры подключены
