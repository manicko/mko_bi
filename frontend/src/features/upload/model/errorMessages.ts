import { ErrorCode } from '../../../shared/types/enums'

/**
 * Upload feature error message map with Russian strings.
 * Contains error codes specific to file upload and processing.
 */
export const uploadErrorMessages: Partial<Record<ErrorCode, string>> = {
  [ErrorCode.FILE_UPLOAD_ERROR]: 'Не удалось загрузить файл. Попробуйте ещё раз.',
  [ErrorCode.FILE_TOO_LARGE]: 'Размер файла превышает допустимый лимит (максимум 100 МБ)',
  [ErrorCode.INVALID_FILE_TYPE]: 'Неверный тип файла. Разрешены только CSV и GZIP файлы.',
  [ErrorCode.FILE_PROCESSING_ERROR]: 'Ошибка обработки файла. Проверьте формат данных.',
  [ErrorCode.PROCESSING_FAILED]: 'Не удалось обработать файл. Обратитесь к администратору.',
  [ErrorCode.PROCESSING_IN_PROGRESS]: 'Файл уже обрабатывается. Подождите завершения.',
}