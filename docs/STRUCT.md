C:\py_dev\mkobi
├── alembic
│   ├── env.py
│   ├── README
│   ├── script.py.mako
│   └── versions
│       ├── 2aa835fe1fac_add_composite_index_on_aggregated_data.py
│       ├── 3f7a1b2c9d0e_add_processing_logs_dashboard_id_index.py
│       ├── 4bfb28b3732d_add_processing_logs_dashboard_id_index.py
│       ├── 57f43a5c499d_change_json_to_jsonb_for_postgresql.py
│       ├── 91f5436a3098_add_unique_constraint_on_aggregated_.py
│       ├── 840a99edb818_standardize_index_naming.py
│       ├── 7130ecb0388c_true_initial_migration.py
│       ├── 20260507141843_add_updated_at_to_users.py
│       ├── 20260508145000_add_updated_at_to_layouts.py
│       ├── a1b2c3d4e5f6_add_config_to_dashboards.py
│       ├── a1e404502aac_add_registration_requests_table.py
│       ├── a2b3c4d5e6f7_fix_unique_constraint_aggregated_data.py
│       ├── c3cc391beded_add_config_column_and_fix_indexes.py
│       ├── ce58bba5d461_add_db_constraints_and_fix_schema_issues.py
│       ├── e86f3c8f7324_schema_adjustments.py
│       └── f50a4054569c_merge_heads.py
├── alembic.ini
├── bidb_schema.sql
├── create_db.sql
├── data
│   ├── logs
│   │   └── app.json.log.1
│   ├── pgre
│   └── tmp_uploads
├── docker-compose.override.yml
├── docker-compose.test.yml
├── docker-compose.yml
├── Dockerfile
├── docs
│   └── SWAGGER_README.md
├── frontend
│   ├── eslint.config.js
│   ├── index.html
│   ├── package-lock.json
│   ├── package.json
│   ├── public
│   │   ├── favicon.svg
│   │   └── icons.svg
│   ├── README.md
│   ├── src
│   │   ├── app
│   │   │   ├── providers.tsx
│   │   │   └── routes.tsx
│   │   ├── assets
│   │   │   ├── hero.png
│   │   │   ├── react.svg
│   │   │   └── vite.svg
│   │   ├── features
│   │   │   ├── admin
│   │   │   │   ├── api
│   │   │   │   │   └── adminApi.ts
│   │   │   │   └── ui
│   │   │   │       ├── AdminPanel.tsx
│   │   │   │       ├── DashboardManagement.tsx
│   │   │   │       ├── LogViewer.tsx
│   │   │   │       ├── RegistrationRequests.tsx
│   │   │   │       └── UserManagement.tsx
│   │   │   ├── auth
│   │   │   │   ├── api
│   │   │   │   │   └── authApi.ts
│   │   │   │   ├── index.ts
│   │   │   │   ├── model
│   │   │   │   │   ├── authToken.ts
│   │   │   │   │   └── useAuth.ts
│   │   │   │   └── ui
│   │   │   │       ├── LoginForm.tsx
│   │   │   │       └── RegisterForm.tsx
│   │   │   ├── dashboards
│   │   │   │   ├── api
│   │   │   │   │   └── dashboardApi.ts
│   │   │   │   ├── index.ts
│   │   │   │   ├── model
│   │   │   │   └── ui
│   │   │   │       ├── charts
│   │   │   │       │   ├── BarChart.tsx
│   │   │   │       │   ├── index.ts
│   │   │   │       │   ├── LineChart.tsx
│   │   │   │       │   ├── PieChart.tsx
│   │   │   │       │   ├── PlotlyChart.tsx
│   │   │   │       │   └── TableChart.tsx
│   │   │   │       ├── DashboardFilters.tsx
│   │   │   │       ├── DashboardList.tsx
│   │   │   │       └── DashboardView.tsx
│   │   │   ├── upload
│   │   │   │   ├── api
│   │   │   │   │   └── uploadApi.ts
│   │   │   │   ├── index.ts
│   │   │   │   └── ui
│   │   │   │       ├── FileDropzone.tsx
│   │   │   │       └── UploadPage.tsx
│   │   │   └── users
│   │   │       ├── api
│   │   │       │   └── userApi.ts
│   │   │       ├── index.ts
│   │   │       └── ui
│   │   │           └── UserProfile.tsx
│   │   ├── main.tsx
│   │   ├── react-plotly.d.ts
│   │   └── shared
│   │       ├── api
│   │       │   ├── axiosInstance.ts
│   │       │   └── index.ts
│   │       ├── components
│   │       │   ├── index.ts
│   │       │   ├── Layout
│   │       │   │   ├── AppLayout.tsx
│   │       │   │   ├── Header.tsx
│   │       │   │   ├── index.ts
│   │       │   │   └── Sidebar.tsx
│   │       │   ├── PlaceholderPage.tsx
│   │       │   ├── ProtectedRoute.tsx
│   │       │   └── RoleBasedAccess.tsx
│   │       └── types
│   │           ├── api.types.ts
│   │           ├── enums.ts
│   │           └── formSchemas.ts
│   ├── tsconfig.app.json
│   ├── tsconfig.json
│   ├── tsconfig.node.json
│   └── vite.config.ts
├── instructions
│   └── RUN.md
├── mypy.ini
├── nginx
│   └── nginx.conf
├── pyproject.toml
├── README.md
├── README_DOCKER.md
├── SPEC.md
├── src
│   └── mkobi
│       ├── api
│       │   ├── deps.py
│       │   └── routes
│       │       ├── admin.py
│       │       ├── auth.py
│       │       ├── dashboards.py
│       │       ├── data.py
│       │       ├── filters.py
│       │       ├── graphs.py
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
│       │   ├── redis_client.py
│       │   ├── security.py
│       │   └── task_queue.py
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
│       │   │   ├── registration_request.py
│       │   │   └── user.py
│       │   ├── repositories
│       │   │   ├── access_repo.py
│       │   │   ├── aggregated_data_repo.py
│       │   │   ├── dashboard_filter_repo.py
│       │   │   ├── dashboard_repo.py
│       │   │   ├── filter_repo.py
│       │   │   ├── graph_repo.py
│       │   │   ├── layout_repo.py
│       │   │   ├── processing_config_repo.py
│       │   │   ├── processing_log_repo.py
│       │   │   ├── registration_request_repo.py
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
│       │   └── user.py
│       ├── py.typed
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
├── tests
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_config.py
│   ├── test_dashboards_api.py
│   ├── test_filters.py
│   ├── test_graphs.py
│   ├── test_layouts.py
│   ├── test_processing_logs.py
│   ├── test_pydantic_models.py
│   ├── test_repositories.py
│   ├── test_security.py
│   ├── test_storage_manager.py
│   ├── test_upload_api.py
│   └── test_users_api.py
├── TODO
│   ├── AUDIT
│   │   ├── TASK_001_db_structure_audit.md
│   │   ├── TASK_001_db_structure_module_dev.md
│   │   ├── TASK_031_audit.md
│   │   ├── TASK_031_audit_full.md
│   │   ├── TASK_037_test_audit.md
│   │   ├── TASK_037_test_audit1.md
│   │   ├── TASK_038_docker_audit.md
│   │   ├── TASK_050_architecture_audit.md
│   │   └── TEST_036_test_audit_arch.md
│   ├── DEV
│   │   ├── 03_mypy_type_errors_DONE.md
│   │   ├── 034_fix_database_test_deadlocks_DONE.md
│   │   ├── 035_fix_test_foreign_key_violations_DONE.md
│   │   ├── 036_fix_test_fixture_cleanup_DONE.md
│   │   ├── 05_mypy_type_errors_fix.md
│   │   ├── 06_test_quality_improvement_DONE.md
│   │   ├── 07_ruff_linting_fix.md
│   │   ├── 08_docker_devops_improvements.md
│   │   ├── 13_security_improvements.md
│   │   ├── 20_code_cleanup_and_fixes.md
│   │   ├── 910_logging_improvements_DONE.md
│   │   ├── LATER_TASK_032_frontend_token_storage_security.md
│   │   ├── 'NONEED TASK_033_enable_typescript_strict_mode.md'
│   │   ├── TASK_014_linter_issues_fix.md
│   │   └── TASK_024_test_coverage_improvement.md
│   ├── DONE
│   │   ├── TASK_001_sync_async_unification.md
│   │   ├── TASK_014_dash_modern_component_architecture_DONE.md
│   │   ├── TASK_051_di_and_interfaces.md
│   │   ├── TASK_052_secrets_management_DONE.md
│   │   └── TASK_DB_REPRODUCER_MAIN.md
│   └── TASK_031_analysis_report.md
└── uv.lock
