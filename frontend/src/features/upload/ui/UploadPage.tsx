import { useState, useCallback } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  Box,
  Typography,
  Button,
  ToggleButton,
  ToggleButtonGroup,
  LinearProgress,
  Paper,
  Alert,
} from '@mui/material'
import { toast } from 'react-hot-toast'
import { FileDropzone } from './FileDropzone'
import { uploadApi } from '../api/uploadApi'
import { UploadMode, FileUploadStatus } from '../../../shared/types/enums'

interface FileUploadState {
  file: File
  progress: number
  status: FileUploadStatus
  error?: string
  processingLogId?: string
}

export function UploadPage() {
  const { id: dashboardId } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const [mode, setMode] = useState<UploadMode>(UploadMode.OVERWRITE)
  const [files, setFiles] = useState<File[]>([])
  const [fileStates, setFileStates] = useState<FileUploadState[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const [uploadComplete, setUploadComplete] = useState(false)

  const handleModeChange = (_: React.MouseEvent<HTMLElement>, newMode: UploadMode | null) => {
    if (newMode !== null) {
      setMode(newMode)
    }
  }

  const handleFilesSelected = useCallback((newFiles: File[]) => {
    setFiles((prev) => [...prev, ...newFiles])
    setFileStates((prev) => [
      ...prev,
      ...newFiles.map((file) => ({
        file,
        progress: 0,
        status: FileUploadStatus.PENDING,
      })),
    ])
  }, [])

  const handleFileRemove = useCallback(
    (fileName: string) => {
      setFiles((prev) => prev.filter((f) => f.name !== fileName))
      setFileStates((prev) => prev.filter((f) => f.file.name !== fileName))
    },
    []
  )

  const handleUpload = async () => {
    if (!dashboardId || files.length === 0) return

    setIsUploading(true)
    setUploadComplete(false)

    for (let i = 0; i < files.length; i++) {
      const file = files[i]

      setFileStates((prev) =>
        prev.map((f, idx) =>
          idx === i ? { ...f, status: FileUploadStatus.UPLOADING, progress: 0 } : f
        )
      )

      try {
        const response = await uploadApi.uploadFile(
          dashboardId,
          file,
          mode,
          (percent) => {
            setFileStates((prev) =>
              prev.map((f, idx) =>
                idx === i ? { ...f, progress: percent } : f
              )
            )
          }
        )

        setFileStates((prev) =>
          prev.map((f, idx) =>
            idx === i
              ? {
                  ...f,
                  status: FileUploadStatus.SUCCESS,
                  progress: 100,
                  processingLogId: response.processing_log_id,
                }
              : f
          )
        )
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Upload failed'
        setFileStates((prev) =>
          prev.map((f, idx) =>
            idx === i ? { ...f, status: FileUploadStatus.ERROR, error: errorMessage } : f
          )
        )
        toast.error(`Failed to upload ${file.name}`)
      }
    }

    setIsUploading(false)
    setUploadComplete(true)
    toast.success('All files uploaded successfully!')

    setTimeout(() => {
      navigate(`/dashboard/${dashboardId}`)
    }, 1500)
  }

  return (
    <Box sx={{ maxWidth: 800, mx: 'auto', p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Upload Data
      </Typography>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Upload Mode
        </Typography>
        <ToggleButtonGroup
          value={mode}
          exclusive
          onChange={handleModeChange}
          sx={{ mb: 2 }}
        >
          <ToggleButton value={UploadMode.OVERWRITE}>
            Overwrite (Reset all data)
          </ToggleButton>
          <ToggleButton value={UploadMode.APPEND}>
            Append (Add new rows)
          </ToggleButton>
        </ToggleButtonGroup>
        <Typography variant="body2" color="textSecondary">
          {mode === UploadMode.OVERWRITE
            ? 'This will reset all chart data for this dashboard'
            : 'New rows will be appended to existing data'}
        </Typography>
      </Paper>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Select Files
        </Typography>
        <FileDropzone
          onFilesSelected={handleFilesSelected}
          onFileRemove={handleFileRemove}
          selectedFiles={files}
        />
      </Paper>

      {fileStates.length > 0 && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Upload Queue
          </Typography>
          {fileStates.map((fileState) => (
            <Box key={fileState.file.name} sx={{ mb: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2">{fileState.file.name}</Typography>
                <Typography variant="body2" color={
                  fileState.status === FileUploadStatus.SUCCESS ? 'success.main' :
                  fileState.status === FileUploadStatus.ERROR ? 'error.main' : 'textSecondary'
                }>
                  {fileState.status === FileUploadStatus.SUCCESS && 'Success'}
                  {fileState.status === FileUploadStatus.ERROR && `Error: ${fileState.error}`}
                  {fileState.status === FileUploadStatus.UPLOADING && 'Uploading...'}
                  {fileState.status === FileUploadStatus.PENDING && 'Pending'}
                </Typography>
              </Box>
              {(fileState.status === FileUploadStatus.UPLOADING || fileState.status === FileUploadStatus.SUCCESS) && (
                <LinearProgress
                  variant="determinate"
                  value={fileState.progress}
                  color={fileState.status === FileUploadStatus.SUCCESS ? 'success' : 'primary'}
                />
              )}
            </Box>
          ))}
        </Paper>
      )}

      {uploadComplete && (
        <Alert severity="success" sx={{ mb: 3 }}>
          All files uploaded successfully! Redirecting to dashboard...
        </Alert>
      )}

      <Box sx={{ display: 'flex', gap: 2 }}>
        <Button
          variant="contained"
          color="primary"
          disabled={files.length === 0 || isUploading}
          onClick={handleUpload}
          size="large"
        >
          {isUploading ? 'Uploading...' : 'Start Upload'}
        </Button>
        <Button
          variant="outlined"
          onClick={() => navigate(`/dashboard/${dashboardId}`)}
          disabled={isUploading}
        >
          Cancel
        </Button>
      </Box>
    </Box>
  )
}
