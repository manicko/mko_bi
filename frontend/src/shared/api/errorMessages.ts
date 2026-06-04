import { ErrorCode } from '../types/enums'

/**
 * Type for partial error message maps.
 * Feature modules can define only relevant error codes.
 */
export type PartialErrorMessages = Partial<Record<ErrorCode, string>>

/**
 * Shared error message map containing general error codes.
 * Used as fallback for codes not defined in feature-specific maps.
 */
export const sharedErrorMessages: Record<ErrorCode, string> = {
  // General errors
  [ErrorCode.INTERNAL_ERROR]: 'Внутренняя ошибка сервера',
  [ErrorCode.SERVICE_UNAVAILABLE]: 'Сервис временно недоступен',
  [ErrorCode.RATE_LIMIT_EXCEEDED]: 'Превышен лимит запросов. Попробуйте позже.',
  // Authentication errors (fallback defaults)
  [ErrorCode.AUTHENTICATION_FAILED]: 'Ошибка аутентификации',
  [ErrorCode.TOKEN_EXPIRED]: 'Токен истёк',
  [ErrorCode.TOKEN_REVOKED]: 'Токен отозван',
  [ErrorCode.INVALID_TOKEN]: 'Неверный токен',
  // Authorization errors (fallback defaults)
  [ErrorCode.PERMISSION_DENIED]: 'Доступ запрещён',
  [ErrorCode.INSUFFICIENT_PERMISSIONS]: 'Недостаточно прав',
  [ErrorCode.ACCESS_DENIED]: 'Доступ запрещён',
  // Resource errors
  [ErrorCode.NOT_FOUND]: 'Ресурс не найден',
  [ErrorCode.DASHBOARD_NOT_FOUND]: 'Дашборд не найден',
  [ErrorCode.USER_NOT_FOUND]: 'Пользователь не найден',
  [ErrorCode.GRAPH_NOT_FOUND]: 'График не найден',
  [ErrorCode.FILTER_NOT_FOUND]: 'Фильтр не найден',
  [ErrorCode.LAYOUT_NOT_FOUND]: 'Макет не найден',
  [ErrorCode.PROCESSING_CONFIG_NOT_FOUND]: 'Конфигурация обработки не найдена',
  // Validation errors
  [ErrorCode.VALIDATION_ERROR]: 'Ошибка валидации',
  [ErrorCode.INVALID_EMAIL]: 'Неверный формат email',
  [ErrorCode.INVALID_PASSWORD]: 'Неверный пароль',
  [ErrorCode.MISSING_REQUIRED_FIELD]: 'Отсутствует обязательное поле',
  [ErrorCode.INVALID_FIELD_VALUE]: 'Неверное значение поля',
  // File errors
  [ErrorCode.FILE_UPLOAD_ERROR]: 'Ошибка загрузки файла',
  [ErrorCode.FILE_TOO_LARGE]: 'Файл слишком большой',
  [ErrorCode.INVALID_FILE_TYPE]: 'Неверный тип файла',
  [ErrorCode.FILE_PROCESSING_ERROR]: 'Ошибка обработки файла',
  // Conflict errors
  [ErrorCode.EMAIL_ALREADY_EXISTS]: 'Email уже используется',
  [ErrorCode.FILTER_ALREADY_BOUND]: 'Фильтр уже привязан',
  [ErrorCode.DUPLICATE_RESOURCE]: 'Дублирующийся ресурс',
  // Processing errors
  [ErrorCode.PROCESSING_FAILED]: 'Обработка данных завершилась с ошибкой',
  [ErrorCode.PROCESSING_IN_PROGRESS]: 'Обработка данных уже выполняется',
}

/**
 * Default Russian fallback message for unknown error codes.
 */
export const DEFAULT_ERROR_MESSAGE = 'Произошла ошибка'

/**
 * Lookup error message by code.
 * Resolution order: feature map → shared map → error.detail → "Произошла ошибка"
 *
 * @param code - The error code to look up
 * @param featureMessages - Optional feature-specific error messages
 * @param detail - Optional detail message from API response
 * @returns User-friendly Russian error message
 */
export function getErrorMessage(
  code: ErrorCode,
  featureMessages?: PartialErrorMessages,
  detail?: string,
): string {
  // First: check feature-specific map for override
  if (featureMessages?.[code]) {
    return featureMessages[code]
  }

  // Second: check shared map
  if (sharedErrorMessages[code]) {
    return sharedErrorMessages[code]
  }

  // Third: use detail if provided
  if (detail) {
    return detail
  }

  // Fourth: fallback to default Russian message
  return DEFAULT_ERROR_MESSAGE
}