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
├── IMPLEMENTATION_SUMMARY_DASHBOARD_SERVICE.md
├── nginx
│   └── nginx.conf
├── 'Pydantic TASKS.md'
├── pyproject.toml
├── SPEC.md
├── src
│   ├── data
│   │   ├── logs
│   │   └── tmp_uploads
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
│   ├── test_deps.py
│   ├── test_permissions.py
│   ├── test_pydantic_models.py
│   └── test_security.py
├── TODO
│   ├── PLAN.md
│   ├── TASK_001_config_DONE.md
│   ├── TASK_002_base_models_DONE.md
│   ├── TASK_003_pydantic_models.md.DONE
│   ├── TASK_004_repositories_DONE.md
│   ├── TASK_005_security_DONE.md
│   ├── TASK_006_auth_service_DONE.md
│   ├── TASK_007_user_service.md.DONE
│   ├── TASK_008_dashboard_service.md.DONE
│   ├── TASK_009_permissions_DONE.md
│   ├── TASK_010_auth_api.md
│   ├── TASK_011_users_api.md
│   ├── TASK_012_dashboards_api.md
│   ├── TASK_013_upload_api.md
│   ├── TASK_014_data_api.md
│   ├── TASK_015_data_loader.md
│   ├── TASK_016_data_processing.md
│   ├── TASK_017_data_storage.md
│   ├── TASK_018_dashboard_base.md
│   ├── TASK_019_chart_components.md
│   ├── TASK_020_dashboard_impl.md
│   ├── TASK_021_main_app.md
│   ├── TASK_022_utils.md
│   ├── TASK_023_tests_models_repos.md
│   ├── TASK_024_tests_services.md
│   ├── TASK_025_tests_api.md
│   └── TASK_026_tests_data_pipeline.md
└── uv.lock
