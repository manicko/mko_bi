C:\py_exp\mko_bi
├── alembic
│   ├── env.py
│   ├── README
│   ├── script.py.mako
│   └── versions
│       ├── 2aa835fe1fac_add_composite_index_on_aggregated_data.py
│       ├── 3f7a1b2c9d0e_add_processing_logs_dashboard_id_index.py
│       ├── 57f43a5c499d_change_json_to_jsonb_for_postgresql.py
│       ├── 840a99edb818_standardize_index_naming.py
│       ├── 7130ecb0388c_true_initial_migration.py
│       ├── a1b2c3d4e5f6_add_config_to_dashboards.py
│       ├── ce58bba5d461_add_db_constraints_and_fix_schema_issues.py
│       └── e86f3c8f7324_schema_adjustments.py
├── alembic.ini
├── best_llm_models.md
├── bidb_schema.sql
├── check_tables.py
├── create_db.sql
├── data
│   ├── logs
│   │   └── app.json.log.1
│   ├── pgre
│   └── tmp_uploads
├── DB_STRUCTURE.md
├── DBSTR.md
├── instructions
│   └── RUN.md
├── nginx
│   └── nginx.conf
├── 'Pydantic TASKS.md'
├── pyproject.toml
├── SPEC.md
├── SPEC_FRONTEND.md
├── src
│   ├── data
│   │   └── logs
│   ├── db
│   └── mko_bi
│       ├── api
│       │   ├── deps.py
│       │   └── routes
│       │       ├── auth.py
│       │       ├── dashboards.py
│       │       ├── data.py
│       │       ├── filters.py
│       │       ├── layouts.py
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
│       │   ├── security.py
│       │   └── task_queue.py
│       ├── dash_app.py
│       ├── dashboards
│       │   ├── base.py
│       │   ├── components
│       │   │   ├── buttons.py
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
│       │   │   ├── layout_repo.py
│       │   │   ├── processing_config_repo.py
│       │   │   ├── processing_log_repo.py
│       │   │   └── user_repo.py
│       │   ├── session.py
│       │   └── starter.py
│       ├── interfaces
│       │   ├── repository_interfaces.py
│       │   └── service_interfaces.py
│       ├── main.py
│       ├── models
│       │   ├── access.py
│       │   ├── auth.py
│       │   ├── dashboard.py
│       │   ├── data.py
│       │   ├── enums.py
│       │   ├── filters.py
│       │   ├── graph.py
│       │   ├── layout.py
│       │   ├── processing_configs.py
│       │   ├── processing_logs.py
│       │   ├── style.py
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
│       │   ├── layout_service.py
│       │   ├── processing_config_service.py
│       │   ├── processing_log_service.py
│       │   └── user_service.py
│       ├── settings
│       │   ├── app.yaml
│       │   └── README.md
│       ├── utils
│       │   ├── decorators.py
│       │   ├── exceptions.py
│       │   ├── file_utils.py
│       │   ├── time_utils.py
│       │   └── validators.py
│       └── workers
│           └── data_worker.py
├── STRUCT.md
├── TASK_TEMPLATE.md
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
│   ├── test_db_starter.py
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
│   ├── AUDIT
│   │   ├── TASK_001_db_structure_audit.md
│   │   ├── TASK_001_db_structure_module_dev.md
│   │   ├── TASK_031_audit.md
│   │   ├── TASK_031_audit_report_01.md
│   │   ├── TASK_031_audit_report_02.md
│   │   ├── TASK_034_audit_old.md
│   │   ├── TASK_037_test_audit.md
│   │   ├── TASK_037_test_audit1.md
│   │   ├── TASK_038_docker_audit.md
│   │   └── TEST_036_test_audit_arch.md
│   ├── DB
│   ├── DEV
│   ├── DONE
│   │   ├── TASK_001_sync_async_unification.md
│   │   ├── TASK_014_dash_modern_component_architecture_DONE.md
│   │   ├── TASK_051_di_and_interfaces.md
│   │   ├── TASK_052_secrets_management_DONE.md
│   │   └── TASK_DB_REPRODUCER_MAIN.md
│   └── TEST
└── uv.lock
