#!/usr/bin/env python
import sys

sys.path.insert(0, "src")

from mko_bi.models import (
    LoginRequest,
    TokenResponse,
    UserCreate,
    UserRead,
    UserDB,
    ChartConfig,
    DashboardConfig,
    DashboardCreate,
    DashboardRead,
    UploadResponse,
    DataFilter,
    DataResponse,
)

# Test LoginRequest
login = LoginRequest(email="test@test.com", password="123456")
print(f"LoginRequest: {login}")
print(f"Email: {login.email}")
print(f"Password: {login.password}")

# Test TokenResponse
token = TokenResponse(access_token="test_token")
print(f"\nTokenResponse: {token}")

# Test UserCreate
user_create = UserCreate(email="user@test.com", password="password123", role="viewer")
print(f"\nUserCreate: {user_create}")

# Test UserRead
user_read = UserRead(id=1, email="user@test.com", role="admin")
print(f"\nUserRead: {user_read}")

# Test UserDB
user_db = UserDB(id=1, email="user@test.com", password_hash="hash123", role="editor")
print(f"\nUserDB: {user_db}")

# Test ChartConfig
chart = ChartConfig(type="bar", x="x_field", y=["y1", "y2"])
print(f"\nChartConfig: {chart}")

# Test DashboardConfig
dashboard_config = DashboardConfig(charts=[chart], filters=["year", "category"])
print(f"\nDashboardConfig: {dashboard_config}")

# Test DashboardCreate
dashboard_create = DashboardCreate(
    name="Test Dashboard", config={"charts": [], "filters": []}
)
print(f"\nDashboardCreate: {dashboard_create}")

# Test DashboardRead
dashboard_read = DashboardRead(
    id=1, name="Test Dashboard", config={"charts": [], "filters": []}
)
print(f"\nDashboardRead: {dashboard_read}")

# Test UploadResponse
upload_resp = UploadResponse()
print(f"\nUploadResponse: {upload_resp}")

# Test DataFilter
data_filter = DataFilter(year=2024, category="test", brand="brand1")
print(f"\nDataFilter: {data_filter}")

# Test DataResponse
data_resp = DataResponse(data=[{"key": "value"}])
print(f"\nDataResponse: {data_resp}")

print("\n✅ All models work correctly!")
