C:\py_exp\mko_bi
├── check_tables.py
├── create_db.sql
├── data
│   ├── logs
│   ├── pgre
│   └── tmp_uploads
├── DB_STRUCTURE.md
├── DBSTR.md
├── interfaces
│   └── service_interfaces.py
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
│       │       ├── filters.py
│       │       ├── processing_configs.py
│       │       ├── processing_logs.py
│       │       ├── upload.py
│       │       └── users.py
│       ├── app.py
│       ├── config.py
│       ├── core
│       │   ├── permissions.py
│       │   └── security.py
│       ├── dash_app.py
│       ├── dashboards
│       │   ├── base.py
│       │   ├── components
│       │   │   ├── charts
│       │   │   │   ├── bar.py
│       │   │   │   ├── base.py
│       │   │   │   ├── line.py
│       │   │   │   ├── pie.py
│       │   │   │   └── table.py
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
│       │   │   ├── filters.py
│       │   │   ├── graphs.py
│       │   │   ├── layout.py
│       │   │   ├── processing_configs.py
│       │   │   ├── processing_logs.py
│       │   │   └── user.py
│       │   ├── repositories
│       │   │   ├── access_repo.py
│       │   │   ├── aggregated_data_repo.py
│       │   │   ├── dashboard_repo.py
│       │   │   ├── filter_repo.py
│       │   │   ├── processing_config_repo.py
│       │   │   ├── processing_log_repo.py
│       │   │   └── user_repo.py
│       │   └── session.py
│       ├── Docerfile
│       ├── docker-compose.yml
│       ├── interfaces_old
│       │   ├── repository_interfaces.py
│       │   └── service_interfaces.py
│       ├── logging_config.py
│       ├── main.py
│       ├── models
│       │   ├── access.py
│       │   ├── auth.py
│       │   ├── dashboard.py
│       │   ├── data.py
│       │   ├── filters.py
│       │   ├── processing_configs.py
│       │   ├── processing_logs.py
│       │   ├── user.py
│       │   └── user_roles.py
│       ├── services
│       │   ├── auth_service.py
│       │   ├── dashboard_service.py
│       │   ├── data_service.py
│       │   ├── filter_service.py
│       │   ├── processing_config_service.py
│       │   ├── processing_log_service.py
│       │   └── user_service.py
│       ├── settings
│       │   └── app.yaml
│       └── utils
│           ├── exceptions.py
│           ├── file_utils.py
│           └── time_utils.py
├── STRUCT.md
├── TASK_TEMPLATE.md
├── TASKS.md
├── tests
│   ├── conftest.py
│   ├── services
│   │   ├── test_auth_service.py
│   │   ├── test_dashboard_service.py
│   │   ├── test_data_service.py
│   │   └── test_user_service.py
│   ├── test_base_models.py
│   ├── test_chart_components.py
│   ├── test_dashboard_base.py
│   ├── test_dashboards_api.py
│   ├── test_data_api.py
│   ├── test_data_loader.py
│   ├── test_data_processing.py
│   ├── test_deps.py
│   ├── test_models.py
│   ├── test_new_models.py
│   ├── test_new_repositories.py
│   ├── test_permissions.py
│   ├── test_processing_log_service.py
│   ├── test_pydantic_models.py
│   ├── test_repositories.py
│   ├── test_security.py
│   ├── test_storage_manager.py
│   └── test_upload_api.py
├── TODO
│   ├── DEV
│   │   ├── TASK_051_di_and_interfaces.md
│   │   ├── TASK_052_fix_linting_and_types.md
│   │   ├── TASK_053_error_handling.md
│   │   ├── TASK_054_manage_global_state.md
│   │   ├── TASK_056_base_classes_and_utils.md
│   │   ├── TASK_058_integration_tests.md
│   │   ├── TASK_059_alembic_migrations.md
│   │   ├── TASK_060_implement_yoy.md
│   │   └── TASK_061_calculate_shares.md
│   ├── TASK_033_audit.md
│   ├── TASK_034_audit.md
│   ├── TASK_036_audit_tz.md
│   ├── TASK_037_test_audit.md
│   ├── TASK_037_test_audit1.md
│   └── TEST
│       ├── TASK_038_repository_integration_tests.md
│       ├── TASK_039_security_tests.md
│       ├── TASK_040_file_upload_edge_cases.md
│       ├── TASK_041_aggregation_accuracy.md
│       ├── TASK_042_yoy_accuracy.md
│       └── TASK_043_rbac_access_control.md
└── uv.lock
