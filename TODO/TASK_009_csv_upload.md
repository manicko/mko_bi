# Task: CSV Upload Endpoint

## Goal
Handle CSV file uploads and trigger data processing

## Implementation Details

### Files to Modify
- `src/mko_bi/api/routes/upload.py`

### Endpoints

#### POST /upload
- **Authentication**: Required (JWT)
- **Authorization**: Editor or Admin (can upload data)
- **Input**: multipart/form-data with file field
- **Output**: Processing status
- **Logic**:
  1. Validate JWT and user role (editor/admin)
  2. Validate file is present
  3. Validate file type is .csv.gz
  4. Validate file size (< 100MB)
  5. Save to temporary directory (UPLOAD_TEMP_DIR)
  6. Trigger processing via `trigger_processing()`
  7. Delete temporary file
  8. Return success status

### File Validation
- Extension: .csv.gz only
- Size: <= 100MB
- Content type: application/gzip

### Temporary Files
- Location: `/tmp/mko_bi_uploads/` (from config)
- Cleanup: Delete after processing
- Naming: Use UUID or timestamp to avoid conflicts

### Error Handling
- 400 for missing file
- 400 for invalid file type
- 413 for file too large
- 401 for invalid auth
- 403 for insufficient permissions
- 500 for processing errors

### Testing
- Test valid upload
- Test invalid file type
- Test oversized file
- Test missing file
- Test auth requirements
- Verify file cleanup
- Test processing trigger