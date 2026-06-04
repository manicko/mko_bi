import { ErrorCode } from '../../../shared/types/enums'

/**
 * Users feature error message map with Russian strings.
 * Contains error codes specific to user profile operations.
 */
export const userErrorMessages: Partial<Record<ErrorCode, string>> = {
  [ErrorCode.USER_NOT_FOUND]: 'Пользователь не найден',
  [ErrorCode.INVALID_PASSWORD]: 'Текущий пароль неверен',
  [ErrorCode.VALIDATION_ERROR]: 'Ошибка валидации данных профиля',
}