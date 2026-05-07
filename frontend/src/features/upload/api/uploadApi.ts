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
