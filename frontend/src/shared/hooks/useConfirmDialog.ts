import { useCallback, useState } from 'react'

interface ConfirmOptions {
  title: string
  message: string
  confirmLabel?: string
  onConfirm?: () => void
}

interface ConfirmDialogState {
  isOpen: boolean
  title: string
  message: string
  confirmLabel: string
  onConfirm: (() => void) | null
}

export function useConfirmDialog() {
  const [state, setState] = useState<ConfirmDialogState>({
    isOpen: false,
    title: '',
    message: '',
    confirmLabel: 'Delete',
    onConfirm: null,
  })

  const confirm = useCallback((options: ConfirmOptions) => {
    setState({
      isOpen: true,
      title: options.title,
      message: options.message,
      confirmLabel: options.confirmLabel ?? 'Delete',
      onConfirm: options.onConfirm ?? null,
    })
  }, [])

  const handleConfirm = useCallback(() => {
    setState((prev) => {
      if (prev.onConfirm) {
        prev.onConfirm()
      }
      return { ...prev, isOpen: false }
    })
  }, [])

  const handleCancel = useCallback(() => {
    setState((prev) => ({ ...prev, isOpen: false }))
  }, [])

  return {
    confirm,
    isOpen: state.isOpen,
    title: state.title,
    message: state.message,
    confirmLabel: state.confirmLabel,
    handleConfirm,
    handleCancel,
  }
}