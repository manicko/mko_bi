TASK: создание GraphService

FILE: src/mko_bi/services/graph_service.py

GOAL: реализовать сервис для работы с графиками

IMPLEMENT:

class GraphService(IGraphService):
    def __init__(self, repository: IGraphRepository):
        self._repository = repository
    
    def create(self, data: GraphCreate) -> GraphRead:
        ...
    
    def get(self, graph_id: int) -> GraphRead | None:
        ...
    
    def update(self, graph_id: int, data: GraphUpdate) -> GraphRead | None:
        ...
    
    def delete(self, graph_id: int) -> bool:
        ...
    
    def list_by_dashboard(self, dashboard_id: int) -> list[GraphRead]:
        ...

LOGIC:

реализовать все методы интерфейса IGraphService
использовать IGraphRepository для доступа к данным
возвращать Pydantic модели (GraphRead)

CONSTRAINTS:

соответствие интерфейсу IGraphService
использование репозитория, а не прямых запросов

DONE:

GraphService создан
все методы реализованы
соответствует интерфейсу
