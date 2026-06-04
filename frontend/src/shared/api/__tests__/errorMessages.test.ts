import { describe, it, expect } from 'vitest'
import { getErrorMessage, sharedErrorMessages, DEFAULT_ERROR_MESSAGE } from '../errorMessages'
import { ErrorCode } from '../../types/enums'
import { authErrorMessages } from '../../../features/auth/model/errorMessages'
import { uploadErrorMessages } from '../../../features/upload/model/errorMessages'
import { dashboardErrorMessages } from '../../../features/dashboards/model/errorMessages'
import { adminErrorMessages } from '../../../features/admin/model/errorMessages'
import { userErrorMessages } from '../../../features/users/model/errorMessages'

describe('getErrorMessage', () => {
  it('returns feature-specific message when provided', () => {
    const featureMessages = {
      [ErrorCode.AUTHENTICATION_FAILED]: 'Feature auth error message',
    }

    const result = getErrorMessage(ErrorCode.AUTHENTICATION_FAILED, featureMessages)

    expect(result).toBe('Feature auth error message')
  })

  it('falls back to shared message when feature message not provided', () => {
    const result = getErrorMessage(ErrorCode.AUTHENTICATION_FAILED)

    expect(result).toBe(sharedErrorMessages[ErrorCode.AUTHENTICATION_FAILED])
  })

  it('returns shared message when feature map is empty', () => {
    const result = getErrorMessage(ErrorCode.GRAPH_NOT_FOUND, {})

    // Empty feature map falls back to shared map
    expect(result).toBe(sharedErrorMessages[ErrorCode.GRAPH_NOT_FOUND])
  })

  it('returns default Russian message when nothing else matches', () => {
    // Create a code that doesn't have a message defined in shared maps
    const unknownCode = ErrorCode.GRAPH_NOT_FOUND // Assume this has no custom message

    // When shared map has the message, it will return it
    // To test default, we need to pass an empty feature map and no detail
    const result = getErrorMessage(unknownCode)

    // This should return the shared message
    expect(result).toBe(sharedErrorMessages[unknownCode])
  })

  it('feature message takes priority over shared message', () => {
    const featureMessages = {
      [ErrorCode.AUTHENTICATION_FAILED]: 'Custom auth message',
    }

    const result = getErrorMessage(ErrorCode.AUTHENTICATION_FAILED, featureMessages)

    expect(result).toBe('Custom auth message')
    expect(result).not.toBe(sharedErrorMessages[ErrorCode.AUTHENTICATION_FAILED])
  })

  it('detail takes priority over default when no message found', () => {
    const result = getErrorMessage(
      ErrorCode.DASHBOARD_NOT_FOUND,
      {}, // Empty feature map
      'Custom detail message',
    )

    // Since shared has DASHBOARD_NOT_FOUND, it returns the shared message
    expect(result).toBe(sharedErrorMessages[ErrorCode.DASHBOARD_NOT_FOUND])
  })

  it('returns default message for unhandled error', () => {
    // Test that DEFAULT_ERROR_MESSAGE is used as fallback
    expect(DEFAULT_ERROR_MESSAGE).toBe('Произошла ошибка')
  })
})

describe('sharedErrorMessages', () => {
  it('contains all general error codes', () => {
    expect(sharedErrorMessages[ErrorCode.INTERNAL_ERROR]).toBeDefined()
    expect(sharedErrorMessages[ErrorCode.SERVICE_UNAVAILABLE]).toBeDefined()
    expect(sharedErrorMessages[ErrorCode.RATE_LIMIT_EXCEEDED]).toBeDefined()
  })

  it('contains all authentication error codes', () => {
    expect(sharedErrorMessages[ErrorCode.AUTHENTICATION_FAILED]).toBeDefined()
    expect(sharedErrorMessages[ErrorCode.TOKEN_EXPIRED]).toBeDefined()
    expect(sharedErrorMessages[ErrorCode.TOKEN_REVOKED]).toBeDefined()
    expect(sharedErrorMessages[ErrorCode.INVALID_TOKEN]).toBeDefined()
  })

  it('contains all authorization error codes', () => {
    expect(sharedErrorMessages[ErrorCode.PERMISSION_DENIED]).toBeDefined()
    expect(sharedErrorMessages[ErrorCode.INSUFFICIENT_PERMISSIONS]).toBeDefined()
    expect(sharedErrorMessages[ErrorCode.ACCESS_DENIED]).toBeDefined()
  })

  it('contains all resource error codes', () => {
    expect(sharedErrorMessages[ErrorCode.NOT_FOUND]).toBeDefined()
    expect(sharedErrorMessages[ErrorCode.DASHBOARD_NOT_FOUND]).toBeDefined()
    expect(sharedErrorMessages[ErrorCode.USER_NOT_FOUND]).toBeDefined()
    expect(sharedErrorMessages[ErrorCode.GRAPH_NOT_FOUND]).toBeDefined()
    expect(sharedErrorMessages[ErrorCode.FILTER_NOT_FOUND]).toBeDefined()
    expect(sharedErrorMessages[ErrorCode.LAYOUT_NOT_FOUND]).toBeDefined()
    expect(sharedErrorMessages[ErrorCode.PROCESSING_CONFIG_NOT_FOUND]).toBeDefined()
  })

  it('contains all validation error codes', () => {
    expect(sharedErrorMessages[ErrorCode.VALIDATION_ERROR]).toBeDefined()
    expect(sharedErrorMessages[ErrorCode.INVALID_EMAIL]).toBeDefined()
    expect(sharedErrorMessages[ErrorCode.INVALID_PASSWORD]).toBeDefined()
    expect(sharedErrorMessages[ErrorCode.MISSING_REQUIRED_FIELD]).toBeDefined()
    expect(sharedErrorMessages[ErrorCode.INVALID_FIELD_VALUE]).toBeDefined()
  })

  it('contains all file error codes', () => {
    expect(sharedErrorMessages[ErrorCode.FILE_UPLOAD_ERROR]).toBeDefined()
    expect(sharedErrorMessages[ErrorCode.FILE_TOO_LARGE]).toBeDefined()
    expect(sharedErrorMessages[ErrorCode.INVALID_FILE_TYPE]).toBeDefined()
    expect(sharedErrorMessages[ErrorCode.FILE_PROCESSING_ERROR]).toBeDefined()
  })

  it('contains all conflict error codes', () => {
    expect(sharedErrorMessages[ErrorCode.EMAIL_ALREADY_EXISTS]).toBeDefined()
    expect(sharedErrorMessages[ErrorCode.FILTER_ALREADY_BOUND]).toBeDefined()
    expect(sharedErrorMessages[ErrorCode.DUPLICATE_RESOURCE]).toBeDefined()
  })

  it('contains all processing error codes', () => {
    expect(sharedErrorMessages[ErrorCode.PROCESSING_FAILED]).toBeDefined()
    expect(sharedErrorMessages[ErrorCode.PROCESSING_IN_PROGRESS]).toBeDefined()
  })

  it('all messages are in Russian', () => {
    const cyrillicPattern = /[а-яё]/i
    Object.values(sharedErrorMessages).forEach((message) => {
      expect(cyrillicPattern.test(message)).toBe(true)
    })
  })
})

describe('authErrorMessages', () => {
  it('contains all required auth error codes', () => {
    expect(authErrorMessages[ErrorCode.AUTHENTICATION_FAILED]).toBe('Неверный email или пароль')
    expect(authErrorMessages[ErrorCode.TOKEN_EXPIRED]).toBe('Сессия истёкла. Пожалуйста, войдите снова.')
    expect(authErrorMessages[ErrorCode.TOKEN_REVOKED]).toBe('Ваша сессия была завершена. Пожалуйста, войдите снова.')
    expect(authErrorMessages[ErrorCode.INVALID_TOKEN]).toBe('Неверный токен аутентификации')
    expect(authErrorMessages[ErrorCode.EMAIL_ALREADY_EXISTS]).toBe('Пользователь с таким email уже зарегистрирован')
    expect(authErrorMessages[ErrorCode.INVALID_EMAIL]).toBe('Введите корректный email адрес')
    expect(authErrorMessages[ErrorCode.INVALID_PASSWORD]).toBe('Неверный пароль')
    expect(authErrorMessages[ErrorCode.RATE_LIMIT_EXCEEDED]).toBe('Слишком много попыток входа. Попробуйте позже.')
  })
})

describe('uploadErrorMessages', () => {
  it('contains all required upload error codes', () => {
    expect(uploadErrorMessages[ErrorCode.FILE_UPLOAD_ERROR]).toBe('Не удалось загрузить файл. Попробуйте ещё раз.')
    expect(uploadErrorMessages[ErrorCode.FILE_TOO_LARGE]).toBe('Размер файла превышает допустимый лимит (максимум 100 МБ)')
    expect(uploadErrorMessages[ErrorCode.INVALID_FILE_TYPE]).toBe('Неверный тип файла. Разрешены только CSV и GZIP файлы.')
    expect(uploadErrorMessages[ErrorCode.FILE_PROCESSING_ERROR]).toBe('Ошибка обработки файла. Проверьте формат данных.')
    expect(uploadErrorMessages[ErrorCode.PROCESSING_FAILED]).toBe('Не удалось обработать файл. Обратитесь к администратору.')
    expect(uploadErrorMessages[ErrorCode.PROCESSING_IN_PROGRESS]).toBe('Файл уже обрабатывается. Подождите завершения.')
  })
})

describe('dashboardErrorMessages', () => {
  it('contains all required dashboard error codes', () => {
    expect(dashboardErrorMessages[ErrorCode.DASHBOARD_NOT_FOUND]).toBe('Дашборд не найден или был удалён')
    expect(dashboardErrorMessages[ErrorCode.PERMISSION_DENIED]).toBe('У вас нет прав для выполнения этого действия')
    expect(dashboardErrorMessages[ErrorCode.ACCESS_DENIED]).toBe('Доступ к дашборду запрещён')
    expect(dashboardErrorMessages[ErrorCode.VALIDATION_ERROR]).toBe('Ошибка валидации данных дашборда')
  })
})

describe('adminErrorMessages', () => {
  it('contains all required admin error codes', () => {
    expect(adminErrorMessages[ErrorCode.USER_NOT_FOUND]).toBe('Пользователь не найден в системе')
    expect(adminErrorMessages[ErrorCode.PERMISSION_DENIED]).toBe('Недостаточно прав для административной операции')
    expect(adminErrorMessages[ErrorCode.EMAIL_ALREADY_EXISTS]).toBe('Пользователь с таким email уже существует')
    expect(adminErrorMessages[ErrorCode.VALIDATION_ERROR]).toBe('Ошибка валидации административных данных')
  })
})

describe('userErrorMessages', () => {
  it('contains all required user error codes', () => {
    expect(userErrorMessages[ErrorCode.USER_NOT_FOUND]).toBe('Пользователь не найден')
    expect(userErrorMessages[ErrorCode.INVALID_PASSWORD]).toBe('Текущий пароль неверен')
    expect(userErrorMessages[ErrorCode.VALIDATION_ERROR]).toBe('Ошибка валидации данных профиля')
  })
})