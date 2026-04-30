TASK: валидация путей файлов (защита от directory traversal)

FILE: src/mko_bi/services/data_service.py

GOAL: безопасная загрузка файлов

IMPLEMENT:

from werkzeug.utils import secure_filename
from pathlib import Path

def _save_uploaded_file(upload_dir: Path, filename: str, file_content: bytes) -> Path:
    # secured filename
    secured_filename = secure_filename(filename)
    
    # формирование пути
    file_path = upload_dir / secured_filename
    
    # проверка что путь в разрешенной директории
    resolved_path = file_path.resolve()
    resolved_upload_dir = upload_dir.resolve()
    
    if not str(resolved_path).startswith(str(resolved_upload_dir)):
        raise ValueError(f"Invalid file path: {filename}")
    
    # сохранение
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    return file_path

LOGIC:

использовать secure_filename для очистки имени файла
проверять что результирующий путь в разрешенной директории
использовать Path.resolve() для проверки

CONSTRAINTS:

защита от directory traversal
использование только разрешенных директорий

DONE:

directory traversal невозможен
пути валидируются корректно
