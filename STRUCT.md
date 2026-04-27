C:\py_exp\mko_bi
├── check_tables.py
├── create_db.sql
├── data
│   ├── logs
│   ├── pgre
│   └── tmp_uploads
├── DB_STRUCTURE.md
├── DBSTR.md
├── fix_deps.py
├── fix_test2.py
├── fix_tests.py
├── IMPLEMENTATION_COMPLETE.md
├── IMPLEMENTATION_SUMMARY.md
├── IMPLEMENTATION_SUMMARY_CHART_COMPONENTS.md
├── IMPLEMENTATION_SUMMARY_DASHBOARD_SERVICE.md
├── IMPLEMENTATION_SUMMARY_DATA_PROCESSING.md
├── nginx
│   └── nginx.conf
├── 'Pydantic TASKS.md'
├── pyproject.toml
├── SPEC.md
├── src
│   ├── data
│   │   └── logs
│   └── mko_bi
│       ├── api
│       │   ├── deps.py
│       │   └── routes
│       │       ├── auth.py
│       │       ├── dashboards.py
│       │       ├── data.py
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
│       │   │   │   ├── base.py
│       │   │   │   └── line.py
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
│       │   │   ├── aggregated_data.py
│       │   │   ├── dashboard.py
│       │   │   ├── graphs.py
│       │   │   ├── layout.py
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
│       │   ├── access.py
│       │   ├── auth.py
│       │   ├── dashboard.py
│       │   ├── data.py
│       │   ├── user.py
│       │   └── user_roles.py
│       ├── services
│       │   ├── access_service.py
│       │   ├── auth_service.py
│       │   ├── dashboard_service.py
│       │   ├── data_service.py
│       │   └── user_service.py
│       ├── settings
│       │   └── app.yaml
│       └── utils
│           ├── exceptions.py
│           ├── file_utils.py
│           └── time_utils.py
├── STRUCT.md
├── TASK_016_SUMMARY.md
├── TASK_TEMPLATE.md
├── TASKS.md
├── tests
│   ├── conftest.py
│   ├── test_base_models.py
│   ├── test_chart_components.py
│   ├── test_dashboard_base.py
│   ├── test_dashboards_api.py
│   ├── test_data_api.py
│   ├── test_data_loader.py
│   ├── test_data_processing.py
│   ├── test_deps.py
│   ├── test_permissions.py
│   ├── test_pydantic_models.py
│   ├── test_security.py
│   ├── test_storage_manager.py
│   └── test_upload_api.py
├── TODO
│   ├── PLAN.md
│   ├── TASK_001_config_CHECKED.md
│   ├── TASK_002_base_models_DONE.md
│   ├── TASK_003_pydantic_models.md
│   ├── TASK_004_repositories_DONE.md
│   ├── TASK_005_security_DONE.md
│   ├── TASK_006_auth_service_DONE.md
│   ├── TASK_007_user_service.md
│   ├── TASK_008_dashboard_service.md
│   ├── TASK_009_permissions_CHECKED.md
│   ├── TASK_010_auth_api_DONE.md
│   ├── TASK_011_users_api_DONE.md
│   ├── TASK_012_dashboards_api.md
│   ├── TASK_013_upload_api_DONE.md
│   ├── TASK_014_data_api_DONE.md
│   ├── TASK_015_data_loader_DONE.md
│   ├── TASK_016_data_processing_DONE.md
│   ├── TASK_017_data_storage_DONE.md
│   ├── TASK_018_dashboard_base_DONE.md
│   ├── TASK_019_chart_components_DONE.md
│   ├── TASK_020_dashboard_impl.md
│   ├── TASK_021_main_app.md
│   ├── TASK_022_utils.md
│   ├── TASK_023_tests_models_repos.md
│   ├── TASK_024_tests_services.md
│   ├── TASK_025_tests_api.md
│   └── TASK_026_tests_data_pipeline.md
└── uv.lock
