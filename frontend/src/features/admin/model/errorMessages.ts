import { ErrorCode } from '../../../shared/types/enums'

/**
 * Admin feature error message map with Russian strings.
 * Contains error codes specific to admin operations.
 */
export const adminErrorMessages: Partial<Record<ErrorCode, string>> = {
  [ErrorCode.USER_NOT_FOUND]: 'Пользователь не найден в системе',
  [ErrorCode.PERMISSION_DENIED]: 'Недостаточно прав для административной операции',
  [ErrorCode.EMAIL_ALREADY_EXISTS]: 'Пользователь с таким email уже существует',
  [ErrorCode.VALIDATION_ERROR]: 'Ошибка валидации административных данных',
}