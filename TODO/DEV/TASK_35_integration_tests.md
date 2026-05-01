TASK: добавление интеграционных тестов

FILE: tests/test_integration_upload_process.py, tests/test_integration_dashboards.py

GOAL: покрытие полного цикла

IMPLEMENT:

# test_integration_upload_process.py
def test_upload_process_get_data():
    # 1. upload file
    response = client.post("/upload/1", files={"file": test_file})
    assert response.status_code == 200
    
    # 2. process file
    response = client.post("/data/process/1")
    assert response.status_code == 200
    
    # 3. get aggregated data
    response = client.get("/data/aggregated?dashboard_id=1")
    assert response.status_code == 200
    assert len(response.json()) > 0

# test_integration_rbac.py
def test_rbac_access():
    # test admin/editor/viewer permissions
    pass

LOGIC:

написать тесты для полного цикла upload → process → get data
написать тесты для RBAC
использовать TestClient из FastAPI

CONSTRAINTS:

тесты должны быть изолированными
использовать тестовую БД

DONE:

интеграционные тесты созданы
полный цикл покрыт тестами
RBAC протестирован
