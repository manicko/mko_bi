C:\py_dev\mko_bi
├── data
│   ├── pgre
│   └── tmp_uploads
├── IMPLEMENTATION_COMPLETE.md
├── IMPLEMENTATION_SUMMARY.md
├── nginx
│   └── nginx.conf
├── 'Pydantic TASKS.md'
├── pyproject.toml
├── SPEC.md
├── src
│   └── mko_bi
│       ├── api
│       │   ├── deps.py
│       │   └── routes
│       │       ├── auth.py
│       │       ├── dashboards.py
│       │       ├── upload.py
│       │       └── users.py
│       ├── app.py
│       ├── config.py
│       ├── core
│       │   ├── permissions.py
│       │   └── security.py
│       ├── dashboards
│       │   ├── base.py
│       │   ├── components
│       │   │   ├── charts
│       │   │   │   ├── bar.py
│       │   │   │   └── dot.py
│       │   │   ├── filters.py
│       │   │   └── layout.py
│       │   ├── implementations
│       │   │   ├── dashboard_1.py
│       │   │   └── dashboard_2.py
│       │   └── registry.py
│       ├── data
│       │   ├── loaders
│       │   │   ├── loader.py
│       │   │   └── validator.py
│       │   ├── processing
│       │   │   ├── base.py
│       │   │   ├── registry.py
│       │   │   └── transformations.py
│       │   └── storage
│       │       └── manager.py
│       ├── db
│       │   ├── base.py
│       │   ├── models
│       │   │   ├── access.py
│       │   │   ├── dashboard.py
│       │   │   └── user.py
│       │   ├── repositories
│       │   │   ├── access_repo.py
│       │   │   ├── dashboard_repo.py
│       │   │   └── user_repo.py
│       │   └── session.py
│       ├── Docerfile
│       ├── docker-compose.yml
│       ├── logging_config.py
│       ├── main.py
│       ├── models
│       │   ├── auth.py
│       │   ├── dashboard.py
│       │   ├── data.py
│       │   └── user.py
│       ├── services
│       │   ├── access_service.py
│       │   ├── auth_service.py
│       │   ├── dashboard_service.py
│       │   ├── data_service.py
│       │   └── user_service.py
│       └── utils
│           ├── exceptions.py
│           ├── file_utils.py
│           └── time_utils.py
├── STRUCT.md
├── TASK_TEMPLATE.md
├── TASKS.md
├── test_comprehensive.py
├── test_imports.py
├── test_models.py
├── test_security.py
├── test_security_only.py
├── test_user_service.py
├── tests
│   ├── api
│   │   ├── test_auth.py
│   │   ├── test_upload.py
│   │   └── test_users.py
│   ├── conftest.py
│   ├── data
│   │   ├── test_pipeline.py
│   │   └── test_processing.py
│   └── services
│       ├── test_auth_service.py
│       ├── test_dashboard_service.py
│       └── test_user_service.py
├── TODO
│   ├── IMPLEMENTATION_SUMMARY.md
│   ├── PLAN.md
│   ├── TASK_001_hash_password_DONE.md
│   ├── TASK_002_jwt_token_DONE.md
│   ├── TASK_003_login_endpoint_DONE.md
│   ├── TASK_004_user_service.md
│   ├── TASK_005_users_api.md
│   ├── TASK_006_dashboard_service.md
│   ├── TASK_007_dashboards_api.md
│   ├── TASK_008_access_control.md
│   ├── TASK_009_csv_upload.md
│   ├── TASK_010_csv_loading.md
│   ├── TASK_011_data_validation.md
│   ├── TASK_012_data_pipeline.md
│   ├── TASK_013_data_transformations.md
│   ├── TASK_014_aggregations_registry.md
│   ├── TASK_015_data_storage.md
│   ├── TASK_016_data_retrieval.md
│   ├── TASK_017_dashboard_base.md
│   ├── TASK_018_dashboard_registry.md
│   ├── TASK_019_bar_chart.md
│   ├── TASK_020_dot_chart.md
│   ├── TASK_021_filters.md
│   ├── TASK_022_layout.md
│   └── TASK_023_implementation.md
└── uv.lock
