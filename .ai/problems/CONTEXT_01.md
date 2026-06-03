Нужно сделать более осмысленные ошибки для пользователя на фронтенде переработать ВСЕ ошибки, которые могут отображаться пользователю в виде осмысленных и привязанных к процессу или событию сообщений.
Сейчас при загрузке файлов, например, просто выдается код ошибки и все. Или еще хуже Upload Queue
test_media_data_utf8.csv.gz
Error: undefined

А нужно, разделить ошибки, когда неверный MIME тип, когда размер большой, когда ошибка сети или что-то еще. 
Задача исследовательская. Надо посмотреть, где у нас могут приходить ошибки с бека и сделать так, чтобы они передавались на фронт осмысленно.
Надо подумать, как доработать текущую архитектуру, чтобы это стало возможно. 
Давай разделим задачу на 2.
1) Стандартизация ошибок бека и приведение их к нормальному виду везде.
2) Обработчик ошибок и передача их на фронт 

Ну например, вот так

У тебя сейчас типичная проблема: **бэкенд возвращает ошибки в одном формате, а фронт их не умеет нормально разбирать**. В результате пользователь видит:

```text
Error
undefined
419
Network Error
Request failed with status code 422
```

а не:

```text
Файл слишком большой (максимум 100 МБ)
Неверный тип файла. Разрешены только .csv и .csv.gz
Файл должен быть в UTF-8
Отсутствует колонка TVR
Ошибка обработки данных: колонка date содержит некорректные значения
```

---

# Как обычно делают в нормальных системах

## 1. На бэке ВСЕ бизнес-ошибки имеют единый формат

Например:

```json
{
  "error": {
    "code": "INVALID_FILE_TYPE",
    "message": "Only CSV and CSV.GZ files are allowed",
    "details": {
      "allowed": [
        ".csv",
        ".csv.gz"
      ]
    }
  }
}
```

или

```json
{
  "error": {
    "code": "FILE_TOO_LARGE",
    "message": "File size exceeds limit",
    "details": {
      "max_size_mb": 100
    }
  }
}
```

или

```json
{
  "error": {
    "code": "INVALID_ENCODING",
    "message": "File must be UTF-8 encoded"
  }
}
```

---

# 2. На фронте показывается message

Axios interceptor:

```ts
export function extractErrorMessage(error: unknown): string {
    if (axios.isAxiosError(error)) {
        return (
            error.response?.data?.error?.message ??
            error.response?.data?.detail ??
            error.message ??
            'Unknown error'
        );
    }

    return 'Unknown error';
}
```

---

Использование:

```ts
try {
    await uploadFile(file);
} catch (error) {
    toast.error(extractErrorMessage(error));
}
```

---

# Для FastAPI есть хороший паттерн

Свой класс ошибок.

```python
class ApiException(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: dict | None = None,
    ):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or {}
```

---

Глобальный обработчик:

```python
@app.exception_handler(ApiException)
async def api_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )
```

---

Тогда в коде:

```python
raise ApiException(
    status_code=400,
    code="INVALID_ENCODING",
    message="File must be UTF-8 encoded",
)
```

---

# Для upload особенно важно

Я обычно делю ошибки на 3 уровня.

---

## Уровень 1. Ошибка до отправки

Проверяет React.

Например:

```text
Размер файла > 100 МБ
Расширение не .csv
```

Тут запрос даже не уходит.

```ts
toast.error('Maximum file size is 100 MB');
```

---

## Уровень 2. Ошибка API

Например:

```text
MIME type mismatch
Rate limit exceeded
JWT expired
```

Приходит с сервера.

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many upload requests"
  }
}
```

---

## Уровень 3. Ошибка обработки

Самые важные.

Например:

```text
Нет колонки TVR
Нет колонки date
Ошибка парсинга даты
Неизвестная категория
```

Пользователь должен видеть именно их.

Например:

```json
{
  "error": {
    "code": "MISSING_COLUMN",
    "message": "Required column 'TVR' is missing"
  }
}
```

---

# Очень рекомендую использовать machine-readable codes

Не только message.

Не так:

```json
{
  "detail": "File invalid"
}
```

а так:

```json
{
  "error": {
    "code": "INVALID_FILE_TYPE",
    "message": "Only CSV files are allowed"
  }
}
```

Потом фронт сможет делать:

```ts
switch (error.code) {
    case 'INVALID_FILE_TYPE':
        ...
    case 'FILE_TOO_LARGE':
        ...
}
```

---

# Для твоего BI проекта я бы стандартизировал вообще все ошибки

```json
{
  "error": {
    "code": "INVALID_FILE_TYPE",
    "message": "Only CSV and CSV.GZ files are allowed",
    "details": {}
  }
}
```

```json
{
  "error": {
    "code": "FILE_TOO_LARGE",
    "message": "Maximum file size is 100 MB",
    "details": {
      "max_size_mb": 100
    }
  }
}
```

```json
{
  "error": {
    "code": "INVALID_ENCODING",
    "message": "File must be UTF-8 encoded"
  }
}
```

```json
{
  "error": {
    "code": "MISSING_COLUMN",
    "message": "Required column 'TVR' is missing"
  }
}
```

```json
{
  "error": {
    "code": "INVALID_DATE_FORMAT",
    "message": "Column 'date' contains invalid dates"
  }
}
```

И тогда на фронте будет один универсальный обработчик ошибок + `toast.error(message)`, а пользователь всегда увидит осмысленный текст вместо `419` или `undefined`.
