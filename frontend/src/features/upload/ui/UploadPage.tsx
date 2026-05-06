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
import type { UploadMode } from '../../../shared/types/api.types'

interface FileUploadState {
  file: File
  progress: number
  status: 'pending' | 'uploading' | 'success' | 'error'
  error?: string
  processingLogId?: string
}

export function UploadPage() {
  const { id: dashboardId } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const [mode, setMode] = useState<UploadMode>('overwrite')
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
        status: 'pending' as const,
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
          idx === i ? { ...f, status: 'uploading' as const, progress: 0 } : f
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
                  status: 'success' as const,
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
            idx === i ? { ...f, status: 'error' as const, error: errorMessage } : f
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
          <ToggleButton value="overwrite">
            Перезаписать (Reset all data)
          </ToggleButton>
          <ToggleButton value="append">
            Добавить данные (Append rows)
          </ToggleButton>
        </ToggleButtonGroup>
        <Typography variant="body2" color="textSecondary">
          {mode === 'overwrite'
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
                  fileState.status === 'success' ? 'success.main' :
                  fileState.status === 'error' ? 'error.main' : 'textSecondary'
                }>
                  {fileState.status === 'success' && 'Success'}
                  {fileState.status === 'error' && `Error: ${fileState.error}`}
                  {fileState.status === 'uploading' && 'Uploading...'}
                  {fileState.status === 'pending' && 'Pending'}
                </Typography>
              </Box>
              {(fileState.status === 'uploading' || fileState.status === 'success') && (
                <LinearProgress
                  variant="determinate"
                  value={fileState.progress}
                  color={fileState.status === 'success' ? 'success' : 'primary'}
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
