import { useQuery } from '@tanstack/react-query'
import axiosInstance from '../../../shared/api/axiosInstance'
import type { UploadResponse, ProcessingStatusResponse, ProcessingResult } from '../../../shared/types/api.types'
import { UploadMode } from '../../../shared/types/enums'

export const uploadApi = {
  uploadFile: async (
    dashboardId: string,
    file: File,
    mode: UploadMode = UploadMode.OVERWRITE,
    onProgress?: (percent: number) => void
  ): Promise<UploadResponse> => {
    const formData = new FormData()
    formData.append('file', file)

    const response = await axiosInstance.post<UploadResponse>(
      `/upload/${dashboardId}`,
      formData,
      {
        params: { mode },
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent: { loaded: number; total?: number }) => {
          if (onProgress && progressEvent.total) {
            const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total)
            onProgress(percent)
          }
        },
      }
    )
    return response.data
  },

  getProcessingStatus: async (logId: string): Promise<ProcessingStatusResponse> => {
    const response = await axiosInstance.get<ProcessingStatusResponse>(`/upload/status/${logId}`)
    return response.data
  },

  getProcessingResult: async (logId: string): Promise<ProcessingResult> => {
    const response = await axiosInstance.get<ProcessingResult>(`/upload/result/${logId}`)
    return response.data
  },
}

// Hook for polling processing status
export function useProcessingStatus(logId: string | null, enabled: boolean = true) {
  return useQuery({
    queryKey: ['processingStatus', logId],
    queryFn: () => uploadApi.getProcessingStatus(logId!),
    enabled: enabled && !!logId,
    refetchInterval: (data) => {
      // Stop polling when processing is complete or failed
      if (data?.state.data?.status === 'completed' || data?.state.data?.status === 'success' || data?.state.data?.status === 'failed') {
        return false
      }
      return 2000 // Poll every 2 seconds
    },
  })
}
