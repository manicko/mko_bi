TASK: Добавление проверки MIME-type для загружаемых файлов

FILE: src/mko_bi/services/data_service.py
FILE: src/mko_bi/api/routes/upload.py

GOAL: Соответствие SPEC.md п.6 — обязательная проверка MIME-type (text/csv, application/gzip)

IMPLEMENT:

func: validate_mime_type(filename, content_type, file_content)

LOGIC:

1. В data_service.py добавить функцию проверки MIME-type:
```
def _validate_mime_type(content_type: str | None, file_content: bytes) -> None:
    allowed_mime_types = ["text/csv", "application/gzip", "application/x-gzip"]
    
    if content_type and content_type not in allowed_mime_types:
        raise ValueError(f"Недопустимый MIME-type: {content_type}")
```

2. Вызывать проверку в `_validate_file()` ДО проверки расширения

3. В upload.py передавать `file.content_type` в сервис:
```
result = upload_file(
    filename=file.filename,
    file_content=file_content,
    content_type=file.content_type,  # новое поле
    dashboard_id=dashboard_id,
    user_id=current_user.id,
    db=db,
)
```

4. Опционально: добавить проверку magic numbers через python-magic (если требуется усиленная безопасность)

CONSTRAINTS:

- SPEC.md требует проверку MIME-type
- Можно использовать простую проверку content_type (из заголовков)
- Если python-magic добавляется, он должен быть в dependencies

DONE:

- MIME-type проверяется через file.content_type
- Недопустимый MIME-type вызывает HTTP 415
- Сохранена проверка расширения файла как дополнительная
- `uv run pytest tests/` проходит

TEST:

uv run pytest tests/test_upload_api.py -v
