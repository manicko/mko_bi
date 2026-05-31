import { useState, useCallback, useEffect, useRef } from 'react'
import {
  Box,
  Typography,
  Button,
  ToggleButton,
  ToggleButtonGroup,
  LinearProgress,
  Paper,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material'
import { toast } from 'react-hot-toast'
import { FileDropzone } from './FileDropzone'
import { uploadApi, useProcessingStatus } from '../api/uploadApi'
import { UploadMode, FileUploadStatus, ProcessingStatus } from '../../../shared/types/enums'

interface FileUploadState {
  file: File
  progress: number
  status: FileUploadStatus
  error?: string
  processingLogId?: string
  processingStatus?: ProcessingStatus
}

interface UploadModalProps {
  open: boolean
  onClose: () => void
  dashboardId: string
  onUploadComplete?: () => void
}

export function UploadModal({ open, onClose, dashboardId, onUploadComplete }: UploadModalProps) {
  const [mode, setMode] = useState<UploadMode>(UploadMode.OVERWRITE)
  const [files, setFiles] = useState<File[]>([])
  const [fileStates, setFileStates] = useState<FileUploadState[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const [uploadComplete, setUploadComplete] = useState(false)
  const [processingFinished, setProcessingFinished] = useState(false)

  // Store onUploadComplete in a ref to avoid stale closure issues in polling effect
  const onUploadCompleteRef = useRef(onUploadComplete)
  useEffect(() => {
    onUploadCompleteRef.current = onUploadComplete
  }, [onUploadComplete])

  // Get the first file's processing log ID for polling
  const processingLogId = fileStates.length > 0 ? fileStates[0].processingLogId ?? null : null
  const { data: statusData } = useProcessingStatus(processingLogId, uploadComplete)

  // Update processing status when polling returns data
  useEffect(() => {
    if (statusData?.status) {
      const status = statusData.status

      // eslint-disable-next-line react-hooks/set-state-in-effect
      setFileStates((prev) =>
        prev.map((f) =>
          f.processingLogId
            ? { ...f, processingStatus: status, status: status === 'failed' ? FileUploadStatus.ERROR : f.status }
            : f
        )
      )

      // Handle completion
      if (status === 'completed') {
        toast.success('Processing complete!')
        setProcessingFinished(true)
        onUploadCompleteRef.current?.()
      }
    }
  }, [statusData])

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
    setProcessingFinished(false)

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
                  processingLogId: response.task_id,
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
    toast.success('All files uploaded! Processing...')
  }

  const handleClose = () => {
    if (!isUploading) {
      // Reset state when closing
      setFiles([])
      setFileStates([])
      setUploadComplete(false)
      setProcessingFinished(false)
      onClose()
    }
  }

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Typography variant="h5">Upload Data</Typography>
      </DialogTitle>
      <DialogContent dividers>
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Upload Mode
          </Typography>
          <ToggleButtonGroup
            value={mode}
            exclusive
            onChange={handleModeChange}
            aria-label="Upload mode selection"
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

        {uploadComplete && processingFinished && (
          <Alert severity="success" sx={{ mb: 3 }}>
            All files processed successfully!
          </Alert>
        )}
      </DialogContent>
      <DialogActions>
        <Button
          variant="outlined"
          onClick={handleClose}
          disabled={isUploading}
        >
          {processingFinished ? 'Close' : 'Cancel'}
        </Button>
        <Button
          variant="contained"
          color="primary"
          disabled={files.length === 0 || isUploading || processingFinished}
          onClick={() => void handleUpload()}
          size="large"
        >
          {isUploading ? 'Uploading...' : 'Start Upload'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}