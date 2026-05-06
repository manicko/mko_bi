---
## BLOCK 15: FRONTEND UPLOAD
---

### TASK: File dropzone component

FILE: `frontend/src/features/upload/ui/FileDropzone.tsx`

GOAL: Drag-and-drop зона для файлов (SPEC_FRONTEND.md п.4.7)

IMPLEMENT:

* react-dropzone интеграция
* Поддержка множественной загрузки
* Только .csv, .csv.gz
* Визуализация очереди загрузки (FileUploader List)
* Валидация (extension, MIME-type на фронтенде)

LOGIC:

1. `useDropzone()` hook
2. accept: `.csv`, `.csv.gz`
3. Отображение выбранных файлов с иконками
4. Кнопка "Удалить" для каждого файла

DONE:

* [ ] Dropzone работает
* [ ] Файлы добавляются
* [ ] Валидация работает

---

### TASK: Upload page

FILE: `frontend/src/features/upload/ui/UploadPage.tsx`

GOAL: Страница загрузки данных (SPEC_FRONTEND.md п.4.7)

IMPLEMENT:

* **Mode Toggle**: "Перезаписать" / "Добавить данные"
  * Перезаписать: сброс всех данных графиков
  * Добавить: append новых строк
* **Dropzone**: FileDropzone компонент
* **Progress Bar** для каждого файла
* Кнопка "Начать загрузку"

LOGIC:

1. Выбор файлов → валидация
2. Загрузка по одному: POST /api/v1/upload/:dashboard_id (multipart/form-data)
3. Параметр `mode` в query: `?mode=overwrite` или `?mode=append`
4. Отслеживание прогресса (через progress event или polling статуса)
5. После всех файлов: сообщение об успехе, редирект на /dashboard/:id

DONE:

* [ ] Mode toggle работает
* [ ] Загрузка файлов работает
* [ ] Progress bar отображается
* [ ] Редирект после успеха

---

### TASK: Upload API

FILE: `frontend/src/features/upload/api/uploadApi.ts`

GOAL: API функции для загрузки

IMPLEMENT:

* `uploadFile(dashboardId: string, file: File, mode: 'overwrite' | 'append'): Promise<UploadResponse>`
  * Использовать `FormData` для multipart
  * `onUploadProgress` для отслеживания прогресса
* `getProcessingStatus(logId: string): Promise<ProcessingLogResponse>`

LOGIC:

1. `axios.post()` с `Content-Type: multipart/form-data`
2. Прогресс через `onUploadProgress` callback
3. Поллинг статуса обработки (опционально)

DONE:

* [ ] Upload API работает
* [ ] Progress tracking работает

---
