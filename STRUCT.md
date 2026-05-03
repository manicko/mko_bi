C:\py_exp\mko_bi
├── alembic
│   ├── env.py
│   ├── README
│   ├── script.py.mako
│   └── versions
│       └── e86f3c8f7324_initial_migration.py
├── alembic.ini
├── bidb_schema.sql
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
│       │   ├── logging_config.py
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
│       │   ├── transformation_configs.py
│       │   ├── types.py
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
├── test_output.txt
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
│   ├── test_share_calculation.py
│   ├── test_simple_async.py
│   ├── test_storage_manager.py
│   ├── test_upload_api.py
│   ├── test_yoy_calculation.py
│   └── tests
├── TODO
│   ├── DATABASES_AUDIT_REPORT_01.md
│   ├── DATABASES_AUDIT_REPORT_02.md
│   ├── DATABASES_AUDIT_REPORT_03.md
│   ├── DB
│   │   ├── 001_setup_alembic.md
│   │   ├── 002_async_db_support_DONE.md
│   │   ├── 003_alembic_async_config.md
│   │   ├── 004_fix_timestamp_timezone.md
│   │   ├── 005_create_dashboard_filters_table.md
│   │   ├── 006_fix_json_jsonb_types.md
│   │   ├── 007_fix_is_active_not_null.md
│   │   ├── 008_setup_test_database.md
│   │   ├── 009_add_composite_index.md
│   │   ├── 010_standardize_index_naming.md
│   │   └── README.md
│   ├── DEV
│   │   └── TASK_033_replace_any_types_DONE.md
│   ├── TASK_001_db_structure_audit.md
│   ├── TASK_001_db_structure_module_dev.md
│   ├── TASK_031_audit.md
│   ├── TASK_033_audit.md
│   ├── TASK_034_audit.md
│   ├── TASK_036_test_audit_Arch_report.md
│   ├── TASK_037_test_audit.md
│   ├── TASK_037_test_audit1.md
│   ├── TASK_038_docker_audit.md
│   ├── TEST
│   └── TEST_036_test_audit_arch.md
└── uv.lock
