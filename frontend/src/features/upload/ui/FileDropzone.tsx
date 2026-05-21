import { useCallback } from 'react'
import { useDropzone, type DropzoneOptions, type FileRejection } from 'react-dropzone'
import {
  Box,
  Typography,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  IconButton,
  Paper,
} from '@mui/material'
import DeleteIcon from '@mui/icons-material/Delete'
import InsertDriveFileIcon from '@mui/icons-material/InsertDriveFile'
import DescriptionIcon from '@mui/icons-material/Description'
import { toast } from 'react-hot-toast'

interface FileDropzoneProps {
  onFilesSelected: (files: File[]) => void
  onFileRemove: (fileName: string) => void
  selectedFiles: File[]
  maxFiles?: number
}

const ACCEPTED_MIME_TYPES = ['text/csv', 'application/gzip', 'application/x-gzip']

export function FileDropzone({ onFilesSelected, onFileRemove, selectedFiles, maxFiles }: FileDropzoneProps) {
  const onDrop = useCallback(
    (acceptedFiles: File[], rejected: FileRejection[]) => {
      // Validate file extensions manually (for .csv.gz which might not be caught by accept)
      const validFiles = acceptedFiles.filter((file) => {
        const fileName = file.name.toLowerCase()
        const isValid =
          fileName.endsWith('.csv') ||
          fileName.endsWith('.csv.gz') ||
          (file.type && ACCEPTED_MIME_TYPES.includes(file.type))

        if (!isValid) {
          toast.error(`File ${file.name} has invalid format. Only .csv and .csv.gz are allowed.`)
        }
        return isValid
      })

      if (validFiles.length > 0) {
        onFilesSelected(validFiles)
      }

      if (rejected.length > 0) {
        rejected.forEach((rejection) => {
          const errors = rejection.errors.map((e) => e.message).join(', ')
          toast.error(`File ${rejection.file.name}: ${errors}`)
        })
      }
    },
    [onFilesSelected]
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/gzip': ['.gz'],
      'application/x-gzip': ['.gz'],
    },
    maxFiles,
  })

  const getFileIcon = (fileName: string) => {
    if (fileName.endsWith('.csv.gz')) return <DescriptionIcon />
    if (fileName.endsWith('.csv')) return <InsertDriveFileIcon />
    return <InsertDriveFileIcon />
  }

  return (
    <Box>
      <Paper
        {...getRootProps()}
        sx={{
          p: 3,
          border: '2px dashed',
          borderColor: isDragActive ? 'primary.main' : 'grey.300',
          backgroundColor: isDragActive ? 'action.hover' : 'background.paper',
          cursor: 'pointer',
          textAlign: 'center',
          transition: 'all 0.2s ease-in-out',
          '&:hover': {
            borderColor: 'primary.main',
            backgroundColor: 'action.hover',
          },
        }}
      >
        <input {...getInputProps()} />
        <Typography variant="h6" color="textSecondary">
          {isDragActive ? 'Drop files here...' : 'Drag & drop files here, or click to select'}
        </Typography>
        <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
          Only .csv and .csv.gz files are allowed
        </Typography>
      </Paper>

      {selectedFiles.length > 0 && (
        <List sx={{ mt: 2 }}>
          {selectedFiles.map((file) => (
            <ListItem
              key={file.name}
              sx={{
                border: '1px solid',
                borderColor: 'grey.300',
                borderRadius: 1,
                mb: 1,
              }}
              secondaryAction={
                <IconButton edge="end" onClick={() => onFileRemove(file.name)}>
                  <DeleteIcon />
                </IconButton>
              }
            >
              <ListItemIcon>{getFileIcon(file.name)}</ListItemIcon>
              <ListItemText
                primary={file.name}
                secondary={`${(file.size / 1024).toFixed(2)} KB`}
              />
            </ListItem>
          ))}
        </List>
      )}
    </Box>
  )
}
