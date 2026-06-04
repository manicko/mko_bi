import { ErrorCode } from '../../../shared/types/enums'

/**
 * Auth feature error message map with Russian strings.
 * Contains error codes specific to authentication flows.
 */
export const authErrorMessages: Partial<Record<ErrorCode, string>> = {
  [ErrorCode.AUTHENTICATION_FAILED]: 'Неверный email или пароль',
  [ErrorCode.TOKEN_EXPIRED]: 'Сессия истёкла. Пожалуйста, войдите снова.',
  [ErrorCode.TOKEN_REVOKED]: 'Ваша сессия была завершена. Пожалуйста, войдите снова.',
  [ErrorCode.INVALID_TOKEN]: 'Неверный токен аутентификации',
  [ErrorCode.EMAIL_ALREADY_EXISTS]: 'Пользователь с таким email уже зарегистрирован',
  [ErrorCode.INVALID_EMAIL]: 'Введите корректный email адрес',
  [ErrorCode.INVALID_PASSWORD]: 'Неверный пароль',
  [ErrorCode.RATE_LIMIT_EXCEEDED]: 'Слишком много попыток входа. Попробуйте позже.',
}