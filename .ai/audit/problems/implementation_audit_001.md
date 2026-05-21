
> frontend@0.0.0 build
> tsc -b && vite build

src/features/admin/api/adminApi.ts(4,3): error TS6196: 'UpdateUserRoleRequest' is declared but never used.
src/features/auth/api/authApi.ts(2,42): error TS6196: 'RegistrationRequest' is declared but never used.
src/features/dashboards/ui/charts/PlotlyChart.tsx(2,23): error TS6196: 'Data' is declared but never used.
src/features/dashboards/ui/DashboardFilters.tsx(16,29): error TS6196: 'FilterConfig' is declared but never used.
src/features/upload/api/uploadApi.ts(52,17): error TS2339: Property 'status' does not exist on type 'Query<ProcessingStatusResponse, Error, ProcessingStatusResponse, (string | null)[]>'.
src/features/upload/api/uploadApi.ts(52,49): error TS2339: Property 'status' does not exist on type 'Query<ProcessingStatusResponse, Error, ProcessingStatusResponse, (string | null)[]>'.
src/features/upload/api/uploadApi.ts(52,79): error TS2339: Property 'status' does not exist on type 'Query<ProcessingStatusResponse, Error, ProcessingStatusResponse, (string | null)[]>'.
src/features/upload/ui/FileDropzone.tsx(2,28): error TS6133: 'DropzoneOptions' is declared but its value is never read.
