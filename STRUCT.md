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
│   ├── test_share_calculation.py
│   ├── test_storage_manager.py
│   ├── test_upload_api.py
│   └── test_yoy_calculation.py
├── TODO
│   ├── DEV
│   │   ├── TASK_031_yoy_share_tests_DONE.md
│   │   ├── TASK_033_replace_any_types.md
│   │   └── TASK_034_fix_exception_handling.md
│   ├── TASK_031_audit.md
│   ├── TASK_033_audit.md
│   ├── TASK_034_audit.md
│   ├── TASK_037_test_audit.md
│   ├── TASK_037_test_audit1.md
│   ├── TASK_038_docker_audit.md
│   └── TEST
└── uv.lock
