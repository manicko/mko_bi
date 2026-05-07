C:\py_dev\mkobi
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
│       ├── 20260507141843_add_updated_at_to_users.py
│       ├── a1b2c3d4e5f6_add_config_to_dashboards.py
│       ├── a1e404502aac_add_registration_requests_table.py
│       ├── ce58bba5d461_add_db_constraints_and_fix_schema_issues.py
│       ├── e86f3c8f7324_schema_adjustments.py
│       └── f50a4054569c_merge_heads.py
├── alembic.ini
├── best_llm_models.md
├── bidb_schema.sql
├── check_paths.py
├── check_tables.py
├── create_db.sql
├── data
│   ├── logs
│   │   └── app.json.log.1
│   ├── pgre
│   └── tmp_uploads
├── DB_STRUCTURE.md
├── DBSTR.md
├── docker-compose.yml
├── Dockerfile
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
│   │           └── enums.ts
│   ├── tsconfig.app.json
│   ├── tsconfig.json
│   ├── tsconfig.node.json
│   └── vite.config.ts
├── instructions
│   └── RUN.md
├── mypy.ini
├── mypy_errors.txt
├── mypy_output.txt
├── nginx
│   └── nginx.conf
├── PRODUCTION_CHECKLIST.md
├── 'Pydantic TASKS.md'
├── pyproject.toml
├── README.md
├── README_DOCKER.md
├── SPEC.md
├── SPEC_FRONTEND.md
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
│       │   ├── user.py
│       │   └── user_roles.py
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
├── TASK_TEMPLATE.md
├── TASKS_TEMPLATE.md
├── test_output.txt
├── tests
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_config.py
│   ├── test_dashboards_api.py
│   ├── test_data_loader.py
│   ├── test_data_processing.py
│   ├── test_filters.py
│   ├── test_graphs.py
│   ├── test_layouts.py
│   ├── test_models.py
│   ├── test_processing_logs.py
│   ├── test_pydantic_models.py
│   ├── test_repositories.py
│   ├── test_security.py
│   ├── test_share_calculation.py
│   ├── test_storage_manager.py
│   ├── test_upload_api.py
│   ├── test_users_api.py
│   └── test_yoy_calculation.py
├── TODO
│   ├── AUDIT
│   │   ├── TASK_001_db_structure_audit.md
│   │   ├── TASK_001_db_structure_module_dev.md
│   │   ├── TASK_031_audit.md
│   │   ├── TASK_031_audit_full.md
│   │   ├── TASK_034_audit_old.md
│   │   ├── TASK_037_test_audit.md
│   │   ├── TASK_037_test_audit1.md
│   │   ├── TASK_038_docker_audit.md
│   │   ├── TASK_050_architecture_audit.md
│   │   └── TEST_036_test_audit_arch.md
│   ├── DEV
│   │   ├── 03_mypy_type_errors.md
│   │   ├── 13_dependency_injection_fixes_DONE.md
│   │   ├── 13_frontend_typescript_fixes_DONE.md
│   │   ├── 14_config_module_fixes.md
│   │   ├── 15_code_quality_tools.md
│   │   ├── 16_logging_improvements_DONE.md
│   │   ├── 17_security_improvements.md
│   │   ├── 18_data_pipeline_fixes.md
│   │   └── DOCKER_PLAN.md
│   ├── DONE
│   │   ├── TASK_001_sync_async_unification.md
│   │   ├── TASK_014_dash_modern_component_architecture_DONE.md
│   │   ├── TASK_051_di_and_interfaces.md
│   │   ├── TASK_052_secrets_management_DONE.md
│   │   └── TASK_DB_REPRODUCER_MAIN.md
│   ├── TASK_01_analysis_report.md
│   ├── TASK_02_analysis_report.md
│   └── TASK_03_analysis_report.md
└── uv.lock
