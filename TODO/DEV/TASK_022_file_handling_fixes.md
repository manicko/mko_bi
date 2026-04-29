TASK: корректная работа с файлами

FILE: src/mko_bi/api/routes/upload.py, src/mko_bi/services/data_service.py

GOAL: закрытие дескрипторов и удаление временных файлов

IMPLEMENT:

# upload.py
async def upload_file(...):
    file_path = None
    try:
        file_content = await file.read()
        file_path = _save_file(...)
        # обработка
    except Exception as e:
        logger.error("Upload failed: %s", e)
        raise
    finally:
        if file_path and file_path.exists():
            file_path.unlink()

# использовать контекстный менеджер
with open(file_path, "wb") as f:
    f.write(file_content)

LOGIC:

использовать контекстный менеджер для файлов
добавить блок finally для очистки
удалять временные файлы при ошибке

CONSTRAINTS:

все файловые дескрипторы закрываются
временные файлы удаляются

DONE:

нет утечек файловых дескрипторов
временные файлы очищаются
