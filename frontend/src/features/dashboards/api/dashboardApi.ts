import { useQuery, useQueryClient } from '@tanstack/react-query'
import axiosInstance from '../../../shared/api/axiosInstance'
import type {
  DashboardSummary,
  DashboardDetail,
  AggregatedDataRequest,
  AggregatedDataResponse,
  FilterDetail,
} from '../../../shared/types/api.types'

export const dashboardApi = {
  getMyDashboards: async (): Promise<DashboardSummary[]> => {
    const response = await axiosInstance.get<DashboardSummary[]>('/dashboards/my')
    return response.data
  },

  getDashboard: async (id: string): Promise<DashboardDetail> => {
    const response = await axiosInstance.get<DashboardDetail>(`/dashboards/${id}`)
    return response.data
  },

  getAggregatedData: async (
    params: AggregatedDataRequest
  ): Promise<AggregatedDataResponse> => {
    const response = await axiosInstance.get<AggregatedDataResponse>('/data/aggregated', {
      params,
    })
    return response.data
  },

  getFilter: async (id: string): Promise<FilterDetail> => {
    const response = await axiosInstance.get<FilterDetail>(`/filters/${id}`)
    return response.data
  },
}

export function useMyDashboards() {
  return useQuery({
    queryKey: ['dashboards', 'my'],
    queryFn: () => dashboardApi.getMyDashboards(),
  })
}

export function useDashboard(id: string) {
  return useQuery({
    queryKey: ['dashboards', id],
    queryFn: () => dashboardApi.getDashboard(id),
    enabled: !!id,
  })
}

export function useAggregatedData(
  dashboardId: string,
  filters?: Record<string, string | string[] | number | number[]>
) {
  return useQuery({
    queryKey: ['aggregatedData', dashboardId, filters],
    queryFn: () =>
      dashboardApi.getAggregatedData({ dashboard_id: dashboardId, filters }),
    enabled: !!dashboardId,
  })
}

export function useInvalidateDashboard() {
  const queryClient = useQueryClient()
  return {
    invalidateDashboard: (id: string) =>
      queryClient.invalidateQueries({ queryKey: ['dashboards', id] }),
    invalidateAggregatedData: (dashboardId: string) =>
      queryClient.invalidateQueries({ queryKey: ['aggregatedData', dashboardId] }),
  }
}
