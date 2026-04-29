C:\py_exp\mko_bi
├── check_tables.py
├── create_db.sql
├── data
│   ├── logs
│   ├── pgre
│   └── tmp_uploads
├── DB_STRUCTURE.md
├── DBSTR.md
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
│       │   ├── base_repository.py
│       │   ├── base_service.py
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
│       │   │   ├── graph_repo.py
│       │   │   ├── processing_config_repo.py
│       │   │   ├── processing_log_repo.py
│       │   │   └── user_repo.py
│       │   └── session.py
│       ├── Docerfile
│       ├── docker-compose.yml
│       ├── interfaces
│       │   ├── repository_interfaces.py
│       │   └── service_interfaces.py
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
│       │   ├── graph.py
│       │   ├── processing_configs.py
│       │   ├── processing_logs.py
│       │   ├── user.py
│       │   └── user_roles.py
│       ├── services
│       │   ├── auth_service.py
│       │   ├── dashboard_service.py
│       │   ├── data_service.py
│       │   ├── filter_service.py
│       │   ├── graph_service.py
│       │   ├── processing_config_service.py
│       │   ├── processing_log_service.py
│       │   └── user_service.py
│       ├── settings
│       │   └── app.yaml
│       └── utils
│           ├── decorators.py
│           ├── exceptions.py
│           ├── file_utils.py
│           ├── time_utils.py
│           └── validators.py
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
│   │   ├── TASK_001_graph_models_DONE.md
│   │   ├── TASK_002_fix_imports_DONE.md
│   │   ├── TASK_003_fix_test_mocks.md
│   │   ├── TASK_004_mypy_config_DONE.md
│   │   ├── TASK_005_unify_auth_service_DONE.md
│   │   ├── TASK_006_fix_deps_coupling_DONE.md
│   │   ├── TASK_007_create_graph_service_DONE.md
│   │   ├── TASK_008_fix_db_sessions.md
│   │   ├── TASK_009_fix_ruff_errors.md
│   │   ├── TASK_010_replace_any_types.md
│   │   ├── TASK_011_remove_dead_code.md
│   │   ├── TASK_012_fix_yoy_calculation.md
│   │   ├── TASK_013_fix_gz_processing.md
│   │   ├── TASK_014_implement_shares.md
│   │   ├── TASK_015_safe_csv_processing.md
│   │   ├── TASK_016_path_validation.md
│   │   ├── TASK_017_redis_rate_limiting.md
│   │   ├── TASK_018_cors_production.md
│   │   ├── TASK_020_fix_exception_handling.md
│   │   ├── TASK_021_transaction_management.md
│   │   ├── TASK_022_file_handling_fixes.md
│   │   ├── TASK_023_fix_existing_tests.md
│   │   ├── TASK_024_integration_tests.md
│   │   ├── TASK_025_yoy_share_tests.md
│   │   ├── TASK_026_dash_integration.md
│   │   ├── TASK_027_dash_error_handling.md
│   │   ├── TASK_028_jwt_validation_dash.md
│   │   └── TASK_029_structured_logging.md
│   ├── DEV_PLAN.md
│   ├── TASK_033_an.md
│   ├── TASK_033_analysis_report.md
│   ├── TASK_033_audit.md
│   ├── TASK_034_audit.md
│   ├── TASK_036_tz_audit.md
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
