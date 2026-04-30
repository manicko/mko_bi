TASK: безопасная обработка больших CSV

FILE: src/mko_bi/services/data_service.py

GOAL: предотвращение исчерпания памяти

IMPLEMENT:

import os

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB

def _process_csv_file(file_path: Path, max_size: int = MAX_FILE_SIZE) -> pl.DataFrame:
    # проверка размера файла
    file_size = os.path.getsize(file_path)
    if file_size > max_size:
        raise ValueError(f"File too large: {file_size} bytes")
    
    # использовать scan_csv для больших файлов
    if file_size > 10 * 1024 * 1024:  # 10 MB
        df = pl.scan_csv(file_path).collect()
    else:
        df = pl.read_csv(file_path)
    return df

LOGIC:

проверить размер файла ДО чтения
использовать scan_csv для больших файлов (lazy evaluation)
настроить лимиты в конфигурации

CONSTRAINTS:

лимит размера файла
использование lazy frames для больших файлов

DONE:

большие файлы обрабатываются безопасно
лимиты настроены в конфигурации
