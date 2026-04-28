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
│   ├── DEV_PLAN.md
│   ├── old
│   │   ├── PLAN.md
│   │   ├── TASK_001_config_CHECKED.md
│   │   ├── TASK_002_base_models_DONE.md
│   │   ├── TASK_003_pydantic_models.md
│   │   ├── TASK_004_repositories_DONE.md
│   │   ├── TASK_005_security_DONE.md
│   │   ├── TASK_006_auth_service_DONE.md
│   │   ├── TASK_007_user_service.md
│   │   ├── TASK_008_dashboard_service.md
│   │   ├── TASK_009_permissions_CHECKED.md
│   │   ├── TASK_010_auth_api_DONE.md
│   │   ├── TASK_011_users_api_DONE.md
│   │   ├── TASK_012_dashboards_api.md
│   │   ├── TASK_013_upload_api_DONE.md
│   │   ├── TASK_014_data_api_DONE.md
│   │   ├── TASK_015_data_loader_DONE.md
│   │   ├── TASK_016_data_processing_DONE.md
│   │   ├── TASK_017_data_storage_DONE.md
│   │   ├── TASK_018_dashboard_base_DONE.md
│   │   ├── TASK_019_chart_components_DONE.md
│   │   ├── TASK_020_dashboard_impl_DONE.md
│   │   ├── TASK_021_main_app_DONE.md
│   │   ├── TASK_022_utils_DONE.md
│   │   ├── TASK_023_tests_models_repos_DONE.md
│   │   ├── TASK_024_tests_services.md
│   │   ├── TASK_025_tests_api.md
│   │   ├── TASK_026_tests_data_pipeline.md
│   │   ├── TASK_030_mdmodel_refactor_plan.md
│   │   └── TASK_031_mdmodel_refactor_plan_DONE.md
│   ├── TASK_033_analysis_report.md
│   ├── TASK_033_audit.md
│   ├── TASK_034_audit.md
│   ├── TASK_036_audit_tz.md
│   ├── TASK_036_tz_audit.md
│   ├── TASK_037_test_audit.md
│   ├── TASK_037_test_audit1.md
│   ├── TASK_038_cleanup_files_DONE.md
│   ├── TASK_039_dash_app_DONE.md
│   ├── TASK_040_create_missing_tables_DONE.md
│   ├── TASK_041_add_gin_index_DONE.md
│   ├── TASK_042_remove_hardcoded_secrets_DONE.md
│   ├── TASK_043_implement_yoy.md
│   ├── TASK_044_calculate_shares.md
│   ├── TASK_045_filters_api_DONE.md
│   ├── TASK_046_processing_configs_api_DONE.md
│   ├── TASK_047_processing_logs_api_DONE.md
│   ├── TASK_048_save_aggregated_data_DONE.md
│   ├── TASK_049_database_transactions_DONE.md
│   ├── TASK_050_refactor_business_logic_DONE.md
│   ├── TASK_051_di_and_interfaces.md
│   ├── TASK_052_fix_linting_and_types.md
│   ├── TASK_053_error_handling.md
│   ├── TASK_054_manage_global_state.md
│   ├── TASK_055_security_enhancements.md
│   ├── TASK_056_base_classes_and_utils.md
│   ├── TASK_058_integration_tests.md
│   └── TASK_059_alembic_migrations.md
└── uv.lock
