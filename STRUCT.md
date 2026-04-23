PS C:\py_dev\mko_bi> eza --tree
.
├── data
│   ├── pgre
│   └── tmp_uploads
├── IMPLEMENTATION_COMPLETE.md
├── IMPLEMENTATION_SUMMARY.md
├── nginx
│   └── nginx.conf
├── 'Pydantic TASKS.md'
├── pyproject.toml
├── SPEC.md
├── src
│   ├── mko_bi
│   │   ├── api
│   │   │   ├── deps.py
│   │   │   └── routes
│   │   │       ├── auth.py
│   │   │       ├── dashboards.py
│   │   │       ├── upload.py
│   │   │       └── users.py
│   │   ├── app.py
│   │   ├── config.py
│   │   ├── core
│   │   │   ├── permissions.py
│   │   │   └── security.py
│   │   ├── dashboards
│   │   │   ├── base.py
│   │   │   ├── components
│   │   │   │   ├── charts
│   │   │   │   │   ├── bar.py
│   │   │   │   │   └── dot.py
│   │   │   │   ├── filters.py
│   │   │   │   └── layout.py
│   │   │   ├── implementations
│   │   │   │   ├── dashboard_1.py
│   │   │   │   └── dashboard_2.py
│   │   │   └── registry.py
│   │   ├── data
│   │   │   ├── loaders
│   │   │   │   ├── loader.py
│   │   │   │   └── validator.py
│   │   │   ├── processing
│   │   │   │   ├── base.py
│   │   │   │   ├── registry.py
│   │   │   │   └── transformations.py
│   │   │   └── storage
│   │   │       └── manager.py
│   │   ├── db
│   │   │   ├── base.py
│   │   │   ├── models
│   │   │   │   ├── access.py
│   │   │   │   ├── dashboard.py
│   │   │   │   └── user.py
│   │   │   ├── repositories
│   │   │   │   ├── access_repo.py
│   │   │   │   ├── dashboard_repo.py
│   │   │   │   └── user_repo.py
│   │   │   └── session.py
│   │   ├── Docerfile
│   │   ├── docker-compose.yml
│   │   ├── logging_config.py
│   │   ├── main.py
│   │   ├── models
│   │   │   ├── auth.py
│   │   │   ├── dashboard.py
│   │   │   ├── data.py
│   │   │   └── user.py
│   │   ├── services
│   │   │   ├── access_service.py
│   │   │   ├── auth_service.py
│   │   │   ├── dashboard_service.py
│   │   │   ├── data_service.py
│   │   │   └── user_service.py
│   │   └── utils
│   │       ├── exceptions.py
│   │       ├── file_utils.py
│   │       └── time_utils.py
│   └── mko_bi.egg-info
│       ├── dependency_links.txt
│       ├── entry_points.txt
│       ├── PKG-INFO
│       ├── requires.txt
│       ├── SOURCES.txt
│       └── top_level.txt
├── TASKS.md
├── test_imports.py
├── test_models.py
├── tests
│   ├── api
│   │   ├── test_auth.py
│   │   ├── test_upload.py
│   │   └── test_users.py
│   ├── conftest.py
│   ├── data
│   │   ├── test_pipeline.py
│   │   └── test_processing.py
│   └── services
│       ├── test_auth_service.py
│       └── test_dashboard_service.py
└── uv.lock