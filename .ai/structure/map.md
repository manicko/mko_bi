C:\py_dev\mkobi
├── AGENTS.md
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
│   ├── README_DOCKER.md
│   ├── SPEC.md
│   ├── STRUCT.md
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
├── node_modules
│   ├── @cspotcode
│   │   └── source-map-support
│   │       ├── browser-source-map-support.js
│   │       ├── LICENSE.md
│   │       ├── package.json
│   │       ├── README.md
│   │       ├── register-hook-require.d.ts
│   │       ├── register-hook-require.js
│   │       ├── register.d.ts
│   │       ├── register.js
│   │       ├── source-map-support.d.ts
│   │       └── source-map-support.js
│   ├── @jridgewell
│   │   ├── resolve-uri
│   │   │   ├── LICENSE
│   │   │   ├── package.json
│   │   │   └── README.md
│   │   ├── sourcemap-codec
│   │   │   ├── LICENSE
│   │   │   ├── package.json
│   │   │   ├── README.md
│   │   │   ├── src
│   │   │   │   ├── scopes.ts
│   │   │   │   ├── sourcemap-codec.ts
│   │   │   │   ├── strings.ts
│   │   │   │   └── vlq.ts
│   │   │   └── types
│   │   │       ├── scopes.d.cts
│   │   │       ├── scopes.d.cts.map
│   │   │       ├── scopes.d.mts
│   │   │       ├── scopes.d.mts.map
│   │   │       ├── sourcemap-codec.d.cts
│   │   │       ├── sourcemap-codec.d.cts.map
│   │   │       ├── sourcemap-codec.d.mts
│   │   │       ├── sourcemap-codec.d.mts.map
│   │   │       ├── strings.d.cts
│   │   │       ├── strings.d.cts.map
│   │   │       ├── strings.d.mts
│   │   │       ├── strings.d.mts.map
│   │   │       ├── vlq.d.cts
│   │   │       ├── vlq.d.cts.map
│   │   │       ├── vlq.d.mts
│   │   │       └── vlq.d.mts.map
│   │   └── trace-mapping
│   │       ├── LICENSE
│   │       ├── package.json
│   │       └── README.md
│   ├── @ts-morph
│   │   └── common
│   │       ├── LICENSE
│   │       ├── package.json
│   │       └── readme.md
│   ├── @tsconfig
│   │   ├── node10
│   │   │   ├── LICENSE
│   │   │   ├── package.json
│   │   │   ├── README.md
│   │   │   └── tsconfig.json
│   │   ├── node12
│   │   │   ├── LICENSE
│   │   │   ├── package.json
│   │   │   ├── README.md
│   │   │   └── tsconfig.json
│   │   ├── node14
│   │   │   ├── LICENSE
│   │   │   ├── package.json
│   │   │   ├── README.md
│   │   │   └── tsconfig.json
│   │   └── node16
│   │       ├── LICENSE
│   │       ├── package.json
│   │       ├── README.md
│   │       └── tsconfig.json
│   ├── @types
│   │   ├── js-yaml
│   │   │   ├── index.d.mts
│   │   │   ├── index.d.ts
│   │   │   ├── LICENSE
│   │   │   ├── package.json
│   │   │   └── README.md
│   │   └── node
│   │       ├── assert
│   │       │   └── strict.d.ts
│   │       ├── assert.d.ts
│   │       ├── async_hooks.d.ts
│   │       ├── buffer.buffer.d.ts
│   │       ├── buffer.d.ts
│   │       ├── child_process.d.ts
│   │       ├── cluster.d.ts
│   │       ├── compatibility
│   │       │   └── iterators.d.ts
│   │       ├── console.d.ts
│   │       ├── constants.d.ts
│   │       ├── crypto.d.ts
│   │       ├── dgram.d.ts
│   │       ├── diagnostics_channel.d.ts
│   │       ├── dns
│   │       │   └── promises.d.ts
│   │       ├── dns.d.ts
│   │       ├── domain.d.ts
│   │       ├── events.d.ts
│   │       ├── fs
│   │       │   └── promises.d.ts
│   │       ├── fs.d.ts
│   │       ├── globals.d.ts
│   │       ├── globals.typedarray.d.ts
│   │       ├── http.d.ts
│   │       ├── http2.d.ts
│   │       ├── https.d.ts
│   │       ├── index.d.ts
│   │       ├── inspector
│   │       │   └── promises.d.ts
│   │       ├── inspector.d.ts
│   │       ├── inspector.generated.d.ts
│   │       ├── LICENSE
│   │       ├── module.d.ts
│   │       ├── net.d.ts
│   │       ├── os.d.ts
│   │       ├── package.json
│   │       ├── path
│   │       │   ├── posix.d.ts
│   │       │   └── win32.d.ts
│   │       ├── path.d.ts
│   │       ├── perf_hooks.d.ts
│   │       ├── process.d.ts
│   │       ├── punycode.d.ts
│   │       ├── querystring.d.ts
│   │       ├── quic.d.ts
│   │       ├── readline
│   │       │   └── promises.d.ts
│   │       ├── readline.d.ts
│   │       ├── README.md
│   │       ├── repl.d.ts
│   │       ├── sea.d.ts
│   │       ├── sqlite.d.ts
│   │       ├── stream
│   │       │   ├── consumers.d.ts
│   │       │   ├── promises.d.ts
│   │       │   └── web.d.ts
│   │       ├── stream.d.ts
│   │       ├── string_decoder.d.ts
│   │       ├── test
│   │       │   └── reporters.d.ts
│   │       ├── test.d.ts
│   │       ├── timers
│   │       │   └── promises.d.ts
│   │       ├── timers.d.ts
│   │       ├── tls.d.ts
│   │       ├── trace_events.d.ts
│   │       ├── ts5.6
│   │       │   ├── buffer.buffer.d.ts
│   │       │   ├── compatibility
│   │       │   │   └── float16array.d.ts
│   │       │   ├── globals.typedarray.d.ts
│   │       │   └── index.d.ts
│   │       ├── ts5.7
│   │       │   ├── compatibility
│   │       │   │   └── float16array.d.ts
│   │       │   └── index.d.ts
│   │       ├── tty.d.ts
│   │       ├── url.d.ts
│   │       ├── util
│   │       │   └── types.d.ts
│   │       ├── util.d.ts
│   │       ├── v8.d.ts
│   │       ├── vm.d.ts
│   │       ├── wasi.d.ts
│   │       ├── web-globals
│   │       │   ├── abortcontroller.d.ts
│   │       │   ├── blob.d.ts
│   │       │   ├── console.d.ts
│   │       │   ├── crypto.d.ts
│   │       │   ├── domexception.d.ts
│   │       │   ├── encoding.d.ts
│   │       │   ├── events.d.ts
│   │       │   ├── fetch.d.ts
│   │       │   ├── importmeta.d.ts
│   │       │   ├── messaging.d.ts
│   │       │   ├── navigator.d.ts
│   │       │   ├── performance.d.ts
│   │       │   ├── storage.d.ts
│   │       │   ├── streams.d.ts
│   │       │   ├── timers.d.ts
│   │       │   └── url.d.ts
│   │       ├── worker_threads.d.ts
│   │       └── zlib.d.ts
│   ├── acorn
│   │   ├── bin
│   │   │   └── acorn
│   │   ├── CHANGELOG.md
│   │   ├── LICENSE
│   │   ├── package.json
│   │   └── README.md
│   ├── acorn-walk
│   │   ├── CHANGELOG.md
│   │   ├── LICENSE
│   │   ├── package.json
│   │   └── README.md
│   ├── arg
│   │   ├── index.d.ts
│   │   ├── index.js
│   │   ├── LICENSE.md
│   │   ├── package.json
│   │   └── README.md
│   ├── argparse
│   │   ├── argparse.js
│   │   ├── CHANGELOG.md
│   │   ├── LICENSE
│   │   ├── package.json
│   │   └── README.md
│   ├── balanced-match
│   │   ├── LICENSE.md
│   │   ├── package.json
│   │   └── README.md
│   ├── brace-expansion
│   │   ├── LICENSE
│   │   ├── package.json
│   │   └── README.md
│   ├── code-block-writer
│   │   ├── esm
│   │   │   ├── deps
│   │   │   │   └── deno.land
│   │   │   │       └── std@0.193.0
│   │   │   │           └── testing
│   │   │   │               └── bdd.d.ts.map
│   │   │   ├── mod.d.ts
│   │   │   ├── mod.d.ts.map
│   │   │   ├── mod.js
│   │   │   ├── mod.test.d.ts.map
│   │   │   ├── package.json
│   │   │   └── utils
│   │   │       ├── string_utils.d.ts
│   │   │       ├── string_utils.d.ts.map
│   │   │       ├── string_utils.js
│   │   │       └── string_utils.test.d.ts.map
│   │   ├── LICENSE
│   │   ├── package.json
│   │   ├── README.md
│   │   └── script
│   │       ├── deps
│   │       │   └── deno.land
│   │       │       └── std@0.193.0
│   │       │           └── testing
│   │       │               └── bdd.d.ts.map
│   │       ├── mod.d.ts
│   │       ├── mod.d.ts.map
│   │       ├── mod.js
│   │       ├── mod.test.d.ts.map
│   │       ├── package.json
│   │       └── utils
│   │           ├── string_utils.d.ts
│   │           ├── string_utils.d.ts.map
│   │           ├── string_utils.js
│   │           └── string_utils.test.d.ts.map
│   ├── create-require
│   │   ├── CHANGELOG.md
│   │   ├── create-require.d.ts
│   │   ├── create-require.js
│   │   ├── LICENSE
│   │   ├── package.json
│   │   └── README.md
│   ├── diff
│   │   ├── CONTRIBUTING.md
│   │   ├── LICENSE
│   │   ├── package.json
│   │   ├── README.md
│   │   ├── release-notes.md
│   │   └── runtime.js
│   ├── fdir
│   │   ├── LICENSE
│   │   ├── package.json
│   │   └── README.md
│   ├── js-yaml
│   │   ├── bin
│   │   │   └── js-yaml.js
│   │   ├── index.js
│   │   ├── LICENSE
│   │   ├── package.json
│   │   └── README.md
│   ├── make-error
│   │   ├── index.d.ts
│   │   ├── index.js
│   │   ├── LICENSE
│   │   ├── package.json
│   │   └── README.md
│   ├── minimatch
│   │   ├── LICENSE.md
│   │   ├── package.json
│   │   └── README.md
│   ├── path-browserify
│   │   ├── CHANGELOG.md
│   │   ├── index.js
│   │   ├── LICENSE
│   │   ├── package.json
│   │   ├── README.md
│   │   ├── security.md
│   │   └── test
│   │       ├── index.js
│   │       ├── test-path-basename.js
│   │       ├── test-path-dirname.js
│   │       ├── test-path-extname.js
│   │       ├── test-path-isabsolute.js
│   │       ├── test-path-join.js
│   │       ├── test-path-parse-format.js
│   │       ├── test-path-relative.js
│   │       ├── test-path-resolve.js
│   │       ├── test-path-zero-length-strings.js
│   │       └── test-path.js
│   ├── picomatch
│   │   ├── index.js
│   │   ├── LICENSE
│   │   ├── package.json
│   │   ├── posix.js
│   │   └── README.md
│   ├── tinyglobby
│   │   ├── LICENSE
│   │   ├── package.json
│   │   └── README.md
│   ├── ts-morph
│   │   ├── LICENSE
│   │   ├── logo.svg
│   │   ├── package.json
│   │   └── readme.md
│   ├── ts-node
│   │   ├── child-loader.mjs
│   │   ├── dist-raw
│   │   │   ├── node-internal-constants.js
│   │   │   ├── node-internal-errors.js
│   │   │   ├── node-internal-modules-cjs-helpers.js
│   │   │   ├── node-internal-modules-cjs-loader.js
│   │   │   ├── node-internal-modules-esm-get_format.js
│   │   │   ├── node-internal-modules-esm-resolve.js
│   │   │   ├── node-internal-modules-package_json_reader.js
│   │   │   ├── node-internal-repl-await.js
│   │   │   ├── node-internalBinding-fs.js
│   │   │   ├── NODE-LICENSE.md
│   │   │   ├── node-nativemodule.js
│   │   │   ├── node-options.js
│   │   │   ├── node-primordials.js
│   │   │   ├── README.md
│   │   │   └── runmain-hack.js
│   │   ├── esm
│   │   │   └── transpile-only.mjs
│   │   ├── esm.mjs
│   │   ├── LICENSE
│   │   ├── node10
│   │   │   └── tsconfig.json
│   │   ├── node12
│   │   │   └── tsconfig.json
│   │   ├── node14
│   │   │   └── tsconfig.json
│   │   ├── node16
│   │   │   └── tsconfig.json
│   │   ├── package.json
│   │   ├── README.md
│   │   ├── register
│   │   │   ├── files.js
│   │   │   ├── index.js
│   │   │   ├── transpile-only.js
│   │   │   └── type-check.js
│   │   ├── transpilers
│   │   │   ├── swc-experimental.js
│   │   │   └── swc.js
│   │   ├── tsconfig.schema.json
│   │   └── tsconfig.schemastore-schema.json
│   ├── typescript
│   │   ├── bin
│   │   │   ├── tsc
│   │   │   └── tsserver
│   │   ├── LICENSE.txt
│   │   ├── package.json
│   │   ├── README.md
│   │   ├── SECURITY.md
│   │   └── ThirdPartyNoticeText.txt
│   ├── undici-types
│   │   ├── agent.d.ts
│   │   ├── api.d.ts
│   │   ├── balanced-pool.d.ts
│   │   ├── cache-interceptor.d.ts
│   │   ├── cache.d.ts
│   │   ├── client-stats.d.ts
│   │   ├── client.d.ts
│   │   ├── connector.d.ts
│   │   ├── content-type.d.ts
│   │   ├── cookies.d.ts
│   │   ├── diagnostics-channel.d.ts
│   │   ├── dispatcher.d.ts
│   │   ├── env-http-proxy-agent.d.ts
│   │   ├── errors.d.ts
│   │   ├── eventsource.d.ts
│   │   ├── fetch.d.ts
│   │   ├── formdata.d.ts
│   │   ├── global-dispatcher.d.ts
│   │   ├── global-origin.d.ts
│   │   ├── h2c-client.d.ts
│   │   ├── handlers.d.ts
│   │   ├── header.d.ts
│   │   ├── index.d.ts
│   │   ├── interceptors.d.ts
│   │   ├── LICENSE
│   │   ├── mock-agent.d.ts
│   │   ├── mock-call-history.d.ts
│   │   ├── mock-client.d.ts
│   │   ├── mock-errors.d.ts
│   │   ├── mock-interceptor.d.ts
│   │   ├── mock-pool.d.ts
│   │   ├── package.json
│   │   ├── patch.d.ts
│   │   ├── pool-stats.d.ts
│   │   ├── pool.d.ts
│   │   ├── proxy-agent.d.ts
│   │   ├── readable.d.ts
│   │   ├── README.md
│   │   ├── retry-agent.d.ts
│   │   ├── retry-handler.d.ts
│   │   ├── round-robin-pool.d.ts
│   │   ├── snapshot-agent.d.ts
│   │   ├── util.d.ts
│   │   ├── utility.d.ts
│   │   ├── webidl.d.ts
│   │   └── websocket.d.ts
│   ├── v8-compile-cache-lib
│   │   ├── CHANGELOG.md
│   │   ├── LICENSE
│   │   ├── package.json
│   │   ├── README.md
│   │   ├── v8-compile-cache.d.ts
│   │   └── v8-compile-cache.js
│   └── yn
│       ├── index.d.ts
│       ├── index.js
│       ├── lenient.js
│       ├── license
│       ├── package.json
│       └── readme.md
├── package-lock.json
├── package.json
├── pyproject.toml
├── README.md
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
└── uv.lock
