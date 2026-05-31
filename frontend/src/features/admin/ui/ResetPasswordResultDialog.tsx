import { useState } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Button,
  TextField,
  Box,
} from '@mui/material'
import ContentCopyIcon from '@mui/icons-material/ContentCopy'
import { toast } from 'react-hot-toast'

interface ResetPasswordResultDialogProps {
  open: boolean
  tempPassword: string
  userEmail: string
  onClose: () => void
}

export function ResetPasswordResultDialog({
  open,
  tempPassword,
  userEmail,
  onClose,
}: ResetPasswordResultDialogProps) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(tempPassword)
      setCopied(true)
      toast.success('Copied')
      setTimeout(() => setCopied(false), 3000)
    } catch {
      toast.error('Failed to copy')
    }
  }

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Password Reset</DialogTitle>
      <DialogContent>
        <DialogContentText sx={{ mb: 2 }}>
          Password for <strong>{userEmail}</strong> has been reset.
          Copy the temporary password and share it securely.
        </DialogContentText>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <TextField
            value={tempPassword}
            fullWidth
            slotProps={{
              input: {
                readOnly: true,
              },
            }}
            size="small"
          />
          <Button
            variant="outlined"
            onClick={() => {
              void handleCopy()
            }}
            startIcon={<ContentCopyIcon />}
          >
            {copied ? 'Copied' : 'Copy'}
          </Button>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} variant="contained">
          Close
        </Button>
      </DialogActions>
    </Dialog>
  )
}