import { ErrorCode } from '../../../shared/types/enums'

/**
 * Dashboards feature error message map with Russian strings.
 * Contains error codes specific to dashboard operations.
 */
export const dashboardErrorMessages: Partial<Record<ErrorCode, string>> = {
  [ErrorCode.DASHBOARD_NOT_FOUND]: 'Дашборд не найден или был удалён',
  [ErrorCode.PERMISSION_DENIED]: 'У вас нет прав для выполнения этого действия',
  [ErrorCode.ACCESS_DENIED]: 'Доступ к дашборду запрещён',
  [ErrorCode.VALIDATION_ERROR]: 'Ошибка валидации данных дашборда',
}