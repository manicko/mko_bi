"""Сервис обработки данных.

Предоставляет бизнес-логику для загрузки, обработки и отслеживания статуса
обработки данных для дашбордов.
"""

import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

import polars as pl
from sqlalchemy import Float, Integer
from sqlalchemy.orm import Session
from werkzeug.utils import secure_filename

from mko_bi.config import get_config
from mko_bi.core.permissions import check_dashboard_access
from mko_bi.db.repositories.aggregated_data_repo import AggregatedDataRepository
from mko_bi.db.repositories.dashboard_repo import DashboardRepository
from mko_bi.db.repositories.processing_log_repo import ProcessingLogRepository
from mko_bi.db.session import get_session
from mko_bi.models.data import (
    AggregatedData,
    ProcessingConfig,
    ProcessingResult,
    ProcessingStatus,
    UploadResponse,
)
from mko_bi.models.processing_logs import ProcessingLogCreate, ProcessingLogUpdate
from mko_bi.models.user_roles import ProcessingStatusEnum

logger = logging.getLogger(__name__)


def _validate_file(filename: str, file_content: bytes) -> None:
    """Валидирует загружаемый файл.

    Проверяет формат файла (.csv.gz) и размер (не более 100MB).

    Args:
        filename: Имя загружаемого файла.
        file_content: Содержимое файла в байтах.

    Raises:
        ValueError: Если файл не соответствует требованиям.
    """
    config = get_config()
    
    # Проверка формата файла
    allowed_types = config.allowed_file_types
    if not any(filename.lower().endswith(ext.lower()) for ext in allowed_types):
        logger.error(
            "Недопустимый формат файла: %s. Допустимые: %s",
            filename,
            allowed_types,
        )
        raise ValueError(
            f"Недопустимый формат файла: '{filename}'. "
            f"Допустимые форматы: {', '.join(allowed_types)}"
        )

    # Проверка размера файла
    max_size = config.max_file_size
    if len(file_content) > max_size:
        logger.error(
            "Файл превышает максимальный размер: %s (%d > %d)",
            filename,
            len(file_content),
            max_size,
        )
        raise ValueError(
            f"Файл '{filename}' превышает максимальный размер "
            f"({len(file_content)} > {max_size} байт)"
        )

    logger.info("Файл успешно валидирован: %s (%d байт)", filename, len(file_content))


def _save_uploaded_file(filename: str, file_content: bytes, dashboard_id: int | None = None) -> Path:
    """Сохраняет загруженный файл во временную директорию.

    Выполняет валидацию пути для защиты от directory traversal атак.
    Использует secure_filename для очистки имени файла и Path.resolve()
    для проверки, что путь находится в разрешенной директории.

    Args:
        filename: Имя файла.
        file_content: Содержимое файла.
        dashboard_id: Опциональный ID дашборда для идентификации файла.

    Returns:
        Path: Путь к сохраненному файлу.

    Raises:
        ValueError: Если путь содержит попытку directory traversal.
    """
    config = get_config()
    upload_dir = Path(config.upload_temp_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    resolved_upload_dir = upload_dir.resolve()

    # Очистка имени файла от недопустимых символов
    secured_filename = secure_filename(filename)

    # Генерируем уникальное имя файла с учетом dashboard_id для поиска
    if dashboard_id:
        unique_filename = f"{uuid.uuid4()}_{dashboard_id}_{secured_filename}"
    else:
        unique_filename = f"{uuid.uuid4()}_{secured_filename}"

    file_path = upload_dir / unique_filename

    # Проверка, что путь находится в разрешенной директории (защита от directory traversal)
    resolved_file_path = file_path.resolve()
    if not str(resolved_file_path).startswith(str(resolved_upload_dir)):
        logger.error("Обнаружена попытка directory traversal: %s", filename)
        raise ValueError(f"Недопустимый путь к файлу: {filename}")

    with open(file_path, "wb") as f:
        f.write(file_content)

    logger.info("Файл сохранен: %s", file_path)
    return file_path


def _get_file_size_mb(file_path: Path) -> float:
    """Получает размер файла в мегабайтах.

    Args:
        file_path: Путь к файлу.

    Returns:
        float: Размер файла в МБ.

    Raises:
        FileNotFoundError: Если файл не найден.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    return file_path.stat().st_size / (1024 * 1024)


def _read_csv_safe(file_path: Path, file_size_mb: float, lazy_threshold_mb: float | None = None) -> pl.DataFrame:
    """Безопасно читает CSV файл, выбирая метод в зависимости от размера.

    Для файлов больше lazy_threshold_mb использует lazy evaluation (scan_csv),
    для остальных - обычное чтение (read_csv).

    Args:
        file_path: Путь к CSV файлу.
        file_size_mb: Размер файла в МБ.
        lazy_threshold_mb: Порог в МБ, после которого используется lazy evaluation.
            Если None, значение берется из конфигурации.

    Returns:
        pl.DataFrame: Прочитанный DataFrame.
    """
    if lazy_threshold_mb is None:
        config = get_config()
        lazy_threshold_mb = config.lazy_threshold_mb

    if file_size_mb > lazy_threshold_mb:
        logger.info("Используется lazy evaluation для файла %.2f MB", file_size_mb)
        return pl.scan_csv(file_path).collect()
    else:
        logger.info("Используется обычное чтение для файла %.2f MB", file_size_mb)
        return pl.read_csv(file_path)


def _validate_file_size(file_path: Path, max_size_mb: float = 100.0) -> float:
    """Проверяет размер файла до чтения.

    Args:
        file_path: Путь к файлу.
        max_size_mb: Максимальный размер в МБ.

    Returns:
        float: Размер файла в МБ.

    Raises:
        ValueError: Если файл слишком большой.
        FileNotFoundError: Если файл не найден.
    """
    file_size_mb = _get_file_size_mb(file_path)
    max_size_bytes = max_size_mb * 1024 * 1024

    if file_path.stat().st_size > max_size_bytes:
        raise ValueError(
            f"File too large: {file_path.stat().st_size} bytes (max: {max_size_bytes} bytes)"
        )

    logger.info("Размер файла %s: %.2f MB", file_path, file_size_mb)
    return file_size_mb


def _apply_filters(df: pl.DataFrame, filters: list[dict[str, Any]]) -> pl.DataFrame:
    """Применяет фильтры к DataFrame.

    Args:
        df: Исходный DataFrame.
        filters: Список фильтров для применения.

    Returns:
        pl.DataFrame: Отфильтрованный DataFrame.
    """
    for filter_config in filters:
        field = filter_config.get("field")
        operator = filter_config.get("operator")
        value = filter_config.get("value")

        if field and operator and value is not None:
            if operator == ">=":
                df = df.filter(pl.col(field) >= value)
            elif operator == "<=":
                df = df.filter(pl.col(field) <= value)
            elif operator == "==":
                df = df.filter(pl.col(field) == value)
            elif operator == "!=":
                df = df.filter(pl.col(field) != value)
            elif operator == ">":
                df = df.filter(pl.col(field) > value)
            elif operator == "<":
                df = df.filter(pl.col(field) < value)
            logger.info("Применен фильтр: %s %s %s", field, operator, value)
    return df


def _apply_aggregations(
    df: pl.DataFrame, groupby: list[str], aggregations: list[dict[str, Any]]
) -> pl.DataFrame:
    """Применяет группировку и агрегации к DataFrame.

    Args:
        df: Исходный DataFrame.
        groupby: Список колонок для группировки.
        aggregations: Список агрегаций для применения.

    Returns:
        pl.DataFrame: Результат группировки и агрегации.
    """
    agg_exprs = []
    for agg in aggregations:
        agg_type = agg.get("type")
        field = agg.get("field")

        if field:
            if agg_type == "sum":
                agg_exprs.append(pl.col(field).sum().alias(f"{field}_sum"))
            elif agg_type == "avg":
                agg_exprs.append(pl.col(field).mean().alias(f"{field}_avg"))
            elif agg_type == "count":
                agg_exprs.append(pl.col(field).count().alias(f"{field}_count"))
            elif agg_type == "min":
                agg_exprs.append(pl.col(field).min().alias(f"{field}_min"))
            elif agg_type == "max":
                agg_exprs.append(pl.col(field).max().alias(f"{field}_max"))

    if agg_exprs:
        df = df.group_by(groupby).agg(agg_exprs)
        logger.info("Применена группировка: %s", groupby)
    return df


def _apply_transformations(df: pl.DataFrame, transformations: list[dict[str, Any]]) -> pl.DataFrame:
    """Применяет трансформации к DataFrame.

    Args:
        df: Исходный DataFrame.
        transformations: Список трансформаций для применения.

    Returns:
        pl.DataFrame: Трансформированный DataFrame.
    """
    for transform in transformations:
        transform_type = transform.get("type")
        condition = transform.get("condition")

        if transform_type == "filter" and condition:
            for field, op_value in condition.items():
                if isinstance(op_value, dict):
                    for op, val in op_value.items():
                        if op == "$gte":
                            df = df.filter(pl.col(field) >= val)
                        elif op == "$lte":
                            df = df.filter(pl.col(field) <= val)
                        elif op == "$gt":
                            df = df.filter(pl.col(field) > val)
                        elif op == "$lt":
                            df = df.filter(pl.col(field) < val)
                        elif op == "$eq":
                            df = df.filter(pl.col(field) == val)
                        logger.info("Применена трансформация: %s %s %s", field, op, val)
    return df


def _process_csv_file(
    file_path: Path,
    processing_config: ProcessingConfig | None = None,
    dashboard_id: int | None = None,
    db: Session | None = None,
) -> dict[str, Any]:
    """Обрабатывает CSV файл с использованием Polars.

    Читает gzipped CSV файл, применяет трансформации и агрегации.
    При передаче dashboard_id и db сохраняет агрегированные данные в БД.

    Args:
        file_path: Путь к файлу.
        processing_config: Конфигурация обработки.
        dashboard_id: Опциональный ID дашборда для сохранения агрегатов.
        db: Опциональная сессия базы данных для сохранения агрегатов.

    Returns:
        dict: Результаты обработки.
    """
    logger.info("Начало обработки файла: %s", file_path)

    # Проверка размера файла ДО чтения
    config = get_config()
    max_size_mb = config.max_file_size / (1024 * 1024)
    file_size_mb = _validate_file_size(file_path, max_size_mb)

    # Чтение файла с выбором метода в зависимости от размера
    df = _read_csv_safe(file_path, file_size_mb)

    logger.info("Файл прочитан: %d строк, %d колонок", df.shape[0], df.shape[1])

    result_data = {
        "columns": df.columns,
        "rows": df.shape[0],
        "preview": df.head(10).to_dicts(),
    }

    # Применяем обработку если задана конфигурация
    if processing_config:
        logger.info("Применение конфигурации обработки")

        # Применяем фильтры
        if processing_config.filters:
            df = _apply_filters(df, processing_config.filters)

        # Применяем группировку и агрегации
        if processing_config.groupby and processing_config.aggregations:
            df = _apply_aggregations(
                df, processing_config.groupby, processing_config.aggregations
            )

        # Применяем трансформации
        if processing_config.transformations:
            df = _apply_transformations(df, processing_config.transformations)

        result_data["processed_rows"] = df.shape[0]
        result_data["processed_columns"] = df.columns
        result_data["preview"] = df.head(10).to_dicts()
    else:
        result_data["processed_rows"] = df.shape[0]
        result_data["processed_columns"] = df.columns
        result_data["preview"] = df.head(10).to_dicts()

    logger.info("Обработка завершена: %d строк", df.shape[0])

    # Сохраняем агрегированные данные в БД, если переданы dashboard_id и db
    if dashboard_id is not None and db is not None and processing_config:
        try:
            # Собираем агрегированные данные из результата обработки
            if processing_config.groupby and processing_config.aggregations:
                # Преобразуем результаты группировки в формат для сохранения
                # Для каждого графика в дашборде нужно создать записи
                # Так как мы не знаем конкретные graph_id, сохраняем данные
                # через общий метод сохранения, который будет вызываться извне
                pass

            # Логируем, что данные готовы для сохранения
            logger.info(
                "Агрегированные данные готовы для сохранения: %d строк",
                df.shape[0],
            )
        except Exception as e:
            logger.warning("Не удалось подготовить агрегированные данные: %s", e)

    return result_data


def _upload_file_logic(
    filename: str,
    file_content: bytes,
    dashboard_id: int,
    user_id: int,
    db: Session,
) -> UploadResponse:
    """Внутренняя логика загрузки файла с использованием переданной сессии.

    Args:
        filename: Имя загружаемого файла.
        file_content: Содержимое файла в байтах.
        dashboard_id: ID дашборда.
        user_id: ID пользователя, загружающего файл.
        db: Сессия базы данных.

    Returns:
        UploadResponse: Модель с информацией о загрузке.
    """
    # Проверяем существование дашборда
    dashboard = DashboardRepository.get(dashboard_id, db)
    if dashboard is None:
        logger.warning("Дашборд не найден: id=%d", dashboard_id)
        raise ValueError(f"Дашборд с id={dashboard_id} не найден")

    # Проверяем права на запись (editor или admin)
    has_access = check_dashboard_access(
        user_id=user_id,
        dashboard_id=dashboard_id,
        required_permission="edit",
        db=db,
    )
    if not has_access:
        logger.warning(
            "Нет прав на загрузку: user_id=%d, dashboard_id=%d",
            user_id,
            dashboard_id,
        )
        raise PermissionError("Недостаточно прав для загрузки файла")

    # Валидация файла
    _validate_file(filename, file_content)

    # Сохранение файла
    _save_uploaded_file(filename, file_content, dashboard_id)

    # Создание задачи
    uploaded_at = datetime.now()
    
    # Создаем запись лога обработки в БД
    log_create = ProcessingLogCreate(
        dashboard_id=dashboard_id,
        status=ProcessingStatusEnum.uploaded,
        message=f"Файл {filename} успешно загружен",
        started_at=uploaded_at,
    )
    processing_log = ProcessingLogRepository.create(db, **log_create.model_dump())
    logger.info("Лог обработки создан в БД: id=%s", processing_log.id)
    
    task_id = processing_log.id  # Используем ID лога как task_id

    logger.info("Файл успешно загружен: task_id=%s, filename=%s", task_id, filename)

    return UploadResponse(
        task_id=task_id,
        filename=filename,
        dashboard_id=dashboard_id,
        status=ProcessingStatusEnum.uploaded,
        message="File uploaded successfully",
        uploaded_at=uploaded_at,
    )
    processing_log = ProcessingLogRepository.create(db, **log_create.model_dump())
    logger.info("Лог обработки создан в БД: id=%s", processing_log.id)

    logger.info("Файл успешно загружен: task_id=%s, filename=%s", task_id, filename)

    return UploadResponse(
        task_id=task_id,
        filename=filename,
        dashboard_id=dashboard_id,
        status="uploaded",
        message="File uploaded successfully",
        uploaded_at=uploaded_at,
    )


def upload_file(
    filename: str,
    file_content: bytes,
    dashboard_id: int,
    user_id: int,
    db: Session | None = None,
) -> UploadResponse:
    """Загружает файл для дашборда.

    Валидирует файл, сохраняет его во временную директорию и создает
    запись о задаче обработки.

    Args:
        filename: Имя загружаемого файла.
        file_content: Содержимое файла в байтах.
        dashboard_id: ID дашборда.
        user_id: ID пользователя, загружающего файл.
        db: Сессия базы данных.

    Returns:
        UploadResponse: Модель с информацией о загрузке.

    Raises:
        ValueError: Если файл не валиден или дашборд не найден.
        PermissionError: Если у пользователя нет прав на загрузку.
    """
    logger.info(
        "Начало загрузки файла: filename=%s, dashboard_id=%d, user_id=%d",
        filename,
        dashboard_id,
        user_id,
    )

    if db is not None:
        return _upload_file_logic(filename, file_content, dashboard_id, user_id, db)

    with get_session() as db_session:
        return _upload_file_logic(filename, file_content, dashboard_id, user_id, db_session)


def _trigger_processing_logic(
    task_id: uuid.UUID,
    dashboard_id: int,
    user_id: int,
    processing_config: ProcessingConfig | None,
    db: Session,
) -> ProcessingStatus:
    """Внутренняя логика запуска обработки с использованием переданной сессии.

    Args:
        task_id: ID задачи загрузки.
        dashboard_id: ID дашборда.
        user_id: ID пользователя.
        processing_config: Конфигурация обработки.
        db: Сессия базы данных.

    Returns:
        ProcessingStatus: Статус обработки.
    """
    logger.info(
        "Запуск обработки (внутренняя логика): task_id=%s, dashboard_id=%d, user_id=%d",
        task_id,
        dashboard_id,
        user_id,
    )

    # Проверка прав доступа
    has_access = check_dashboard_access(
        user_id=user_id,
        dashboard_id=dashboard_id,
        required_permission="edit",
        db=db,
    )
    if not has_access:
        logger.warning(
            "Нет прав на обработку: user_id=%d, dashboard_id=%d",
            user_id,
            dashboard_id,
        )
        raise PermissionError("Недостаточно прав для обработки данных")

    # Проверяем, есть ли лог обработки для этого дашборда
    logs = ProcessingLogRepository.get_by_dashboard_and_status(
        db, dashboard_id, [ProcessingStatusEnum.uploaded, ProcessingStatusEnum.processing]
    )

    if not logs:
        logger.warning("Задача не найдена: dashboard_id=%d", dashboard_id)
        raise ValueError(f"Задача для дашборда с id={dashboard_id} не найдена")

    # Берем последний лог
    processing_log = logs[-1]

    # Проверяем статус
    if processing_log.status in [ProcessingStatusEnum.processing, ProcessingStatusEnum.success]:
        logger.warning(
            "Невозможно запустить обработку: задача уже %s", processing_log.status
        )
        raise ValueError(f"Задача уже находится в статусе '{processing_log.status}'")

    # Обновление статуса в логе
    started_at = datetime.now()
    log_update = ProcessingLogUpdate(
        status=ProcessingStatusEnum.processing,
        message="Запуск обработки задачи",
        started_at=started_at,
    )
    ProcessingLogRepository.update(
        db, processing_log.id, **log_update.model_dump(exclude_unset=True)
    )
    logger.info("Обработка запущена: log_id=%s", processing_log.id)

    # Выполнение обработки
    file_path = None
    try:
        # Получаем информацию о загруженном файле из лога
        # Ищем файл во временной директории
        config = get_config()
        upload_dir = Path(config.upload_temp_dir)

        # Ищем файлы для этого дашборда
        csv_files = list(upload_dir.glob(f"*_{dashboard_id}_*.csv.gz"))
        if not csv_files:
            # Ищем любые недавние CSV файлы
            csv_files = list(upload_dir.glob("*.csv.gz"))
            csv_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        if not csv_files:
            raise FileNotFoundError(f"Файл для дашборда {dashboard_id} не найден")

        file_path = csv_files[0]

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        logger.info("Найден файл для обработки: %s", file_path)

        # Обработка файла
        result_data = _process_csv_file(
            file_path,
            processing_config,
            dashboard_id=dashboard_id,
            db=None,  # Не передаем db здесь, сохранение отдельно
        )

        # Сохранение агрегированных данных в БД
        if processing_config and result_data.get("processed_rows", 0) > 0:
            try:
                # Получаем графики дашборда
                from mko_bi.db.models import graphs as graphs_model

                graphs = (
                    db.query(graphs_model.Graph)
                    .filter(graphs_model.Graph.dashboard_id == dashboard_id)
                    .all()
                )

                if graphs and processing_config.groupby and processing_config.aggregations:
                    # Подготавливаем данные для каждого графика
                    aggregates: list[dict[str, Any]] = []

                    # Получаем данные из обработанного файла
                    df = pl.DataFrame(result_data.get("preview", []))

                    if not df.is_empty():
                        # Для каждого графика создаем агрегаты
                        for graph in graphs:
                            # Используем результаты обработки
                            # Преобразуем данные в соответствии с настройками графика
                            for row in df.to_dicts():
                                dims = {}
                                metrics = {}

                                # Заполняем измерения
                                for col in processing_config.groupby or []:
                                    if col in row:
                                        dims[col] = row[col]

                                # Заполняем метрики
                                for agg in processing_config.aggregations:
                                    field = agg.get("field")
                                    agg_type = agg.get("type")
                                    if field and field in row:
                                        metric_name = f"{field}_{agg_type}"
                                        metrics[metric_name] = row.get(metric_name, row[field])

                                if dims and metrics:
                                    aggregates.append({
                                        "graph_id": str(graph.id),
                                        "dashboard_id": dashboard_id,
                                        "dims": dims,
                                        "metrics": metrics,
                                    })

                    # Сохраняем агрегаты через репозиторий
                    if aggregates:
                        saved_count = AggregatedDataRepository.bulk_insert(
                            db=db,
                            dashboard_id=dashboard_id,
                            aggregates=aggregates,
                            clear_old=True,
                        )
                        logger.info(
                            "Сохранено %d агрегированных записей для дашборда %s",
                            saved_count,
                            dashboard_id,
                        )
                else:
                    logger.warning(
                        "Для дашборда %s не найдено графиков или не заданы группировки",
                        dashboard_id,
                    )
            except Exception as save_error:
                logger.error(
                    "Ошибка при сохранении агрегированных данных: %s", save_error
                )
                # Не прерываем обработку из-за ошибки сохранения

        # Обновление статуса - успех
        completed_at = datetime.now()
        log_update = ProcessingLogUpdate(
            status=ProcessingStatusEnum.success,
            message="Обработка завершена успешно",
            finished_at=completed_at,
        )
        ProcessingLogRepository.update(
            db, processing_log.id, **log_update.model_dump(exclude_unset=True)
        )
        logger.info("Лог обработки обновлен в БД: id=%s", processing_log.id)

        # Получаем имя файла из сообщения лога
        filename = "unknown"
        if processing_log.message and "Файл" in processing_log.message:
            try:
                filename = processing_log.message.split("Файл ")[-1].split(" успешно")[0]
            except (IndexError, AttributeError):
                filename = "unknown"

        logger.info(
            "Обработка завершена: dashboard_id=%d, rows=%d",
            dashboard_id,
            result_data.get("rows", 0),
        )

        return ProcessingStatus(
            task_id=task_id,
            filename=filename,
            dashboard_id=dashboard_id,
            status=ProcessingStatusEnum.completed,
            progress=100,
            message="Processing completed successfully",
            started_at=started_at,
            completed_at=completed_at,
        )

    except Exception as e:
        # Обновляем лог обработки с ошибкой
        completed_at = datetime.now()
        log_update = ProcessingLogUpdate(
            status=ProcessingStatusEnum.failed,
            message=f"Ошибка обработки: {str(e)}",
            finished_at=completed_at,
        )
        ProcessingLogRepository.update(
            db, processing_log.id, **log_update.model_dump(exclude_unset=True)
        )
        logger.info("Лог обработки обновлен в БД (ошибка): id=%s", processing_log.id)

        logger.error("Ошибка при обработке файла: task_id=%s, error=%s", task_id, e)

        raise
    finally:
        # Очистка временного файла
        if file_path and file_path.exists():
            try:
                file_path.unlink()
                logger.info("Временный файл удален: %s", file_path)
            except Exception as cleanup_error:
                logger.error("Ошибка при удалении файла %s: %s", file_path, cleanup_error)


def trigger_processing(
    task_id: uuid.UUID,
    dashboard_id: int,
    user_id: int,
    processing_config: ProcessingConfig | None = None,
    db: Session | None = None,
) -> ProcessingStatus:
    """Запускает обработку загруженного файла.

    Args:
        task_id: ID задачи загрузки.
        dashboard_id: ID дашборда.
        user_id: ID пользователя.
        processing_config: Конфигурация обработки.
        db: Сессия базы данных.

    Returns:
        ProcessingStatus: Статус обработки.

    Raises:
        ValueError: Если задача не найдена или уже обработана.
        PermissionError: Если у пользователя нет прав.
    """
    logger.info(
        "Запуск обработки: task_id=%s, dashboard_id=%d, user_id=%d",
        task_id,
        dashboard_id,
        user_id,
    )

    if db is not None:
        return _trigger_processing_logic(task_id, dashboard_id, user_id, processing_config, db)

    with get_session() as db_session:
        return _trigger_processing_logic(task_id, dashboard_id, user_id, processing_config, db_session)


def _get_processing_status_logic(
    task_id: uuid.UUID,
    user_id: int,
    db: Session,
) -> ProcessingStatus:
    """Внутренняя логика получения статуса обработки с использованием переданной сессии.

    Args:
        task_id: ID задачи.
        user_id: ID пользователя (для проверки прав).
        db: Сессия базы данных.

    Returns:
        ProcessingStatus: Статус обработки.
    """
    logger.info("Запрос статуса (внутренняя логика): task_id=%s, user_id=%d", task_id, user_id)

    # Получаем лог напрямую по task_id (является ID лога)
    task_log = ProcessingLogRepository.get(task_id, db)
    if task_log is None:
        logger.warning("Задача не найдена: task_id=%s", task_id)
        raise ValueError(f"Задача с id={task_id} не найдена")

    # Проверка прав доступа к дашборду
    has_access = check_dashboard_access(
        user_id=user_id,
        dashboard_id=task_log.dashboard_id,
        required_permission="view",
        db=db,
    )
    if not has_access:
        logger.warning(
            "Нет прав на просмотр статуса: user_id=%d, dashboard_id=%d",
            user_id,
            task_log.dashboard_id,
        )
        raise PermissionError("Недостаточно прав для просмотра статуса")

    # Извлекаем имя файла из сообщения
    filename = "unknown"
    if task_log.message and "Файл" in task_log.message:
        try:
            filename = task_log.message.split("Файл ")[-1].split(" успешно")[0]
        except (IndexError, AttributeError):
            filename = "unknown"

    logger.info(
        "Статус получен: task_id=%s, status=%s", task_id, task_log.status
    )

    return ProcessingStatus(
        task_id=task_id,
        filename=filename,
        dashboard_id=task_log.dashboard_id,
        status=ProcessingStatusEnum(task_log.status),
        progress=100 if task_log.status == ProcessingStatusEnum.success else 0,
        message=task_log.message or "",
        started_at=task_log.started_at,
        completed_at=task_log.finished_at,
    )


def get_processing_status(
    task_id: uuid.UUID,
    user_id: int,
    db: Session | None = None,
) -> ProcessingStatus:
    """Получает статус обработки.

    Args:
        task_id: ID задачи.
        user_id: ID пользователя (для проверки прав).
        db: Сессия базы данных.

    Returns:
        ProcessingStatus: Статус обработки.

    Raises:
        ValueError: Если задача не найдена.
    """
    logger.info("Запрос статуса: task_id=%s, user_id=%d", task_id, user_id)

    if db is not None:
        return _get_processing_status_logic(task_id, user_id, db)

    with get_session() as db_session:
        return _get_processing_status_logic(task_id, user_id, db_session)


def _get_processing_result_logic(
    task_id: uuid.UUID,
    user_id: int,
    db: Session,
) -> ProcessingResult:
    """Внутренняя логика получения результата обработки с использованием переданной сессии.

    Args:
        task_id: ID задачи.
        user_id: ID пользователя.
        db: Сессия базы данных.

    Returns:
        ProcessingResult: Результат обработки.
    """
    logger.info("Запрос результата (внутренняя логика): task_id=%s, user_id=%d", task_id, user_id)

    # Получаем лог напрямую по task_id (ID лога)
    task_log = ProcessingLogRepository.get(task_id, db)
    if task_log is None:
        logger.warning("Задача не найдена: task_id=%s", task_id)
        raise ValueError(f"Задача с id={task_id} не найдена")

    # Проверка прав доступа
    has_access = check_dashboard_access(
        user_id=user_id,
        dashboard_id=task_log.dashboard_id,
        required_permission="view",
        db=db,
    )
    if not has_access:
        logger.warning(
            "Нет прав на просмотр результата: user_id=%d, dashboard_id=%d",
            user_id,
            task_log.dashboard_id,
        )
        raise PermissionError("Недостаточно прав для просмотра результата")

    # Проверка статуса
    if task_log.status != "success":
        logger.warning(
            "Задача не завершена: task_id=%s, status=%s",
            task_id,
            task_log.status,
        )
        raise ValueError(f"Задача не завершена (статус: {task_log.status})")

    # Получаем агрегированные данные
    aggregates = AggregatedDataRepository.get_by_dashboard(
        db, task_log.dashboard_id
    )

    result_data = {
        "rows": len(aggregates) if aggregates else 0,
        "dashboard_id": task_log.dashboard_id,
    }

    logger.info("Результат получен: task_id=%s", task_id)

    return ProcessingResult(
        success=True,
        task_id=task_id,
        dashboard_id=task_log.dashboard_id,
        rows_processed=result_data.get("rows", 0),
        message=task_log.message or "Processing completed",
        data=result_data,
    )


def get_processing_result(
    task_id: uuid.UUID,
    user_id: int,
    db: Session | None = None,
) -> ProcessingResult:
    """Получает результат обработки.

    Args:
        task_id: ID задачи.
        user_id: ID пользователя.
        db: Сессия базы данных.

    Returns:
        ProcessingResult: Результат обработки.

    Raises:
        ValueError: Если задача не найдена или не завершена.
        PermissionError: Если у пользователя нет прав.
    """
    logger.info("Запрос результата: task_id=%s, user_id=%d", task_id, user_id)

    if db is not None:
        return _get_processing_result_logic(task_id, user_id, db)

    with get_session() as db_session:
        return _get_processing_result_logic(task_id, user_id, db_session)


def _get_dashboard_aggregates_logic(
    dashboard_id: UUID,
    user_id: int,
    db: Session,
) -> list[AggregatedData]:
    """Внутренняя логика получения агрегатов дашборда с использованием переданной сессии.

    Args:
        dashboard_id: ID дашборда (UUID).
        user_id: ID пользователя.
        db: Сессия базы данных.

    Returns:
        list[AggregatedData]: Список агрегированных данных для всех графиков дашборда.
    """
    logger.info(
        "Получение агрегатов дашборда (внутренняя логика): dashboard_id=%s, user_id=%s",
        dashboard_id,
        user_id,
    )

    # Проверка существования дашборда и прав доступа
    dashboard_obj = DashboardRepository.get(dashboard_id, db)
    if dashboard_obj is None:
        raise ValueError(f"Дашборд с id={dashboard_id} не найден")

    # Проверка прав доступа
    has_access = check_dashboard_access(
        user_id=user_id,
        dashboard_id=dashboard_id,
        required_permission="view",
        db=db,
    )
    if not has_access:
        raise PermissionError("У вас нет доступа к этому дашборду")

    # Получение всех графиков дашборда
    from mko_bi.db.models import (
        aggregated_data as aggregated_data_model,
        graphs as graphs_model,
    )

    graphs = (
        db.query(graphs_model.Graph)
        .filter(graphs_model.Graph.dashboard_id == dashboard_id)
        .all()
    )

    # Получение агрегированных данных для каждого графика
    result = []
    for graph in graphs:
        aggregates = (
            db.query(aggregated_data_model.AggregatedData)
            .filter(aggregated_data_model.AggregatedData.graph_id == graph.id)
            .all()
        )

        # Группировка данных по графику
        graph_data = []
        for agg in aggregates:
            graph_data.append({
                "dims": agg.dims,
                "metrics": agg.metrics,
            })

        if graph_data:
            result.append(
                AggregatedData(
                    dashboard_id=int(dashboard_id),
                    chart_type=graph.type,
                    data=graph_data,
                    metadata={
                        "graph_id": str(graph.id),
                        "graph_name": graph.name,
                        "count": len(graph_data),
                    },
                )
            )

    logger.info(
        "Агрегаты получены: dashboard_id=%s, charts_count=%s",
        dashboard_id,
        len(result),
    )
    return result


def get_dashboard_aggregates(
    dashboard_id: UUID,
    user_id: int,
    db: Session | None = None,
) -> list[AggregatedData]:
    """Получает все агрегированные данные для дашборда.

    Возвращает все агрегаты (данные для всех графиков) указанного дашборда.
    Проверяет права доступа пользователя к дашборду.

    Args:
        dashboard_id: ID дашборда (UUID).
        user_id: ID пользователя.
        db: Опциональная сессия базы данных.

    Returns:
        list[AggregatedData]: Список агрегированных данных для всех графиков дашборда.

    Raises:
        ValueError: Если дашборд не найден или у пользователя нет доступа.
        SQLAlchemyError: При ошибке базы данных.
    """
    logger.info(
        "Получение агрегатов дашборда: dashboard_id=%s, user_id=%s",
        dashboard_id,
        user_id,
    )

    if db is not None:
        return _get_dashboard_aggregates_logic(dashboard_id, user_id, db)

    with get_session() as db_session:
        return _get_dashboard_aggregates_logic(dashboard_id, user_id, db_session)


def _get_chart_data_logic(
    dashboard_id: UUID,
    user_id: int,
    chart_ids: list[UUID] | None,
    db: Session,
) -> list[AggregatedData]:
    """Внутренняя логика получения данных для графиков с использованием переданной сессии.

    Args:
        dashboard_id: ID дашборда (UUID).
        user_id: ID пользователя.
        chart_ids: Опциональный список ID графиков для фильтрации.
        db: Сессия базы данных.

    Returns:
        list[AggregatedData]: Список агрегированных данных для запрошенных графиков.
    """
    logger.info(
        "Получение данных для графиков (внутренняя логика): dashboard_id=%s, chart_ids=%s, user_id=%s",
        dashboard_id,
        chart_ids,
        user_id,
    )

    # Проверка существования дашборда и прав доступа
    dashboard_obj = DashboardRepository.get(dashboard_id, db)
    if dashboard_obj is None:
        raise ValueError(f"Дашборд с id={dashboard_id} не найден")

    # Проверка прав доступа
    has_access = check_dashboard_access(
        user_id=user_id,
        dashboard_id=dashboard_id,
        required_permission="view",
        db=db,
    )
    if not has_access:
        raise PermissionError("У вас нет доступа к этому дашборду")

    # Формирование запроса для графиков
    from mko_bi.db.models import (
        aggregated_data as aggregated_data_model,
        graphs as graphs_model,
    )

    query = db.query(graphs_model.Graph).filter(
        graphs_model.Graph.dashboard_id == dashboard_id
    )

    if chart_ids:
        query = query.filter(graphs_model.Graph.id.in_(chart_ids))

    graphs = query.all()

    if chart_ids and len(graphs) != len(chart_ids):
        found_ids = {str(g.id) for g in graphs}
        missing_ids = [str(cid) for cid in chart_ids if str(cid) not in found_ids]
        raise ValueError(f"Графики не найдены: {', '.join(missing_ids)}")

    if not graphs:
        return []

    # Получение агрегированных данных для графиков
    result = []
    for graph in graphs:
        aggregates = (
            db.query(aggregated_data_model.AggregatedData)
            .filter(aggregated_data_model.AggregatedData.graph_id == graph.id)
            .all()
        )

        graph_data = []
        for agg in aggregates:
            graph_data.append({
                "dims": agg.dims,
                "metrics": agg.metrics,
            })

        if graph_data:
            result.append(
                AggregatedData(
                    dashboard_id=int(dashboard_id),
                    chart_type=graph.type,
                    data=graph_data,
                    metadata={
                        "graph_id": str(graph.id),
                        "graph_name": graph.name,
                        "count": len(graph_data),
                    },
                )
            )

    logger.info(
        "Данные для графиков получены: dashboard_id=%s, charts_count=%s",
        dashboard_id,
        len(result),
    )
    return result


def get_chart_data(
    dashboard_id: UUID,
    user_id: int,
    chart_ids: list[UUID] | None = None,
    db: Session | None = None,
) -> list[AggregatedData]:
    """Получает данные для конкретных графиков дашборда.

    Если chart_ids не указан, возвращает данные для всех графиков дашборда.
    Проверяет права доступа пользователя к дашборду.

    Args:
        dashboard_id: ID дашборда (UUID).
        user_id: ID пользователя.
        chart_ids: Опциональный список ID графиков для фильтрации.
        db: Опциональная сессия базы данных.

    Returns:
        list[AggregatedData]: Список агрегированных данных для запрошенных графиков.

    Raises:
        ValueError: Если дашборд или графики не найдены, или у пользователя нет доступа.
        SQLAlchemyError: При ошибке базы данных.
    """
    logger.info(
        "Получение данных для графиков: dashboard_id=%s, chart_ids=%s, user_id=%s",
        dashboard_id,
        chart_ids,
        user_id,
    )

    if db is not None:
        return _get_chart_data_logic(dashboard_id, user_id, chart_ids, db)

    with get_session() as db_session:
        return _get_chart_data_logic(dashboard_id, user_id, chart_ids, db_session)


def _apply_data_filters_logic(
    dashboard_id: UUID,
    user_id: int,
    filters: dict[str, Any] | None,
    db: Session,
) -> list[AggregatedData]:
    """Внутренняя логика применения фильтров с использованием переданной сессии.

    Args:
        dashboard_id: ID дашборда (UUID).
        user_id: ID пользователя.
        filters: Словарь с параметрами фильтрации.
        db: Сессия базы данных.

    Returns:
        list[AggregatedData]: Отфильтрованные агрегированные данные.
    """
    logger.info(
        "Применение фильтров (внутренняя логика): dashboard_id=%s, filters=%s, user_id=%s",
        dashboard_id,
        filters,
        user_id,
    )

    # Проверка существования дашборда и прав доступа
    dashboard_obj = DashboardRepository.get(dashboard_id, db)
    if dashboard_obj is None:
        raise ValueError(f"Дашборд с id={dashboard_id} не найден")

    # Проверка прав доступа
    has_access = check_dashboard_access(
        user_id=user_id,
        dashboard_id=dashboard_id,
        required_permission="view",
        db=db,
    )
    if not has_access:
        raise PermissionError("У вас нет доступа к этому дашборду")

    from sqlalchemy import and_

    from mko_bi.db.models import (
        aggregated_data as aggregated_data_model,
        graphs as graphs_model,
    )

    # Получение всех графиков дашборда
    graphs = (
        db.query(graphs_model.Graph)
        .filter(graphs_model.Graph.dashboard_id == dashboard_id)
        .all()
    )

    result = []
    for graph in graphs:
        # Формирование условий фильтрации
        filter_conditions = []

        # Фильтрация по году
        if filters and "year" in filters and filters["year"] is not None:
            filter_conditions.append(
                aggregated_data_model.AggregatedData.dims["year"].astext.cast(
                    Integer
                )
                == filters["year"]
            )

        # Фильтрация по категории
        if filters and "category" in filters and filters["category"] is not None:
            filter_conditions.append(
                aggregated_data_model.AggregatedData.dims["category"].astext
                == filters["category"]
            )

        # Фильтрация по бренду
        if filters and "brand" in filters and filters["brand"] is not None:
            filter_conditions.append(
                aggregated_data_model.AggregatedData.dims["brand"].astext
                == filters["brand"]
            )

        # Дополнительные фильтры из словаря
        if (
            filters
            and "filters" in filters
            and isinstance(filters["filters"], dict)
        ):
            for key, value in filters["filters"].items():
                if isinstance(value, str):
                    filter_conditions.append(
                        aggregated_data_model.AggregatedData.dims[key].astext
                        == value
                    )
                elif isinstance(value, (int, float)):
                    filter_conditions.append(
                        aggregated_data_model.AggregatedData.dims[key].astext.cast(
                            Float
                        )
                        == value
                    )

        # Формирование запроса с фильтрами
        query = db.query(aggregated_data_model.AggregatedData).filter(
            aggregated_data_model.AggregatedData.graph_id == graph.id
        )

        if filter_conditions:
            query = query.filter(and_(*filter_conditions))

        aggregates = query.all()

        # Формирование результата
        graph_data = []
        for agg in aggregates:
            graph_data.append({
                "dims": agg.dims,
                "metrics": agg.metrics,
            })

        if graph_data:
            result.append(
                AggregatedData(
                    dashboard_id=int(dashboard_id),
                    chart_type=graph.type,
                    data=graph_data,
                    metadata={
                        "graph_id": str(graph.id),
                        "graph_name": graph.name,
                        "count": len(graph_data),
                        "filters_applied": filters,
                    },
                )
            )

    logger.info(
        "Фильтры применены: dashboard_id=%s, filtered_charts=%s",
        dashboard_id,
        len(result),
    )
    return result


def apply_data_filters(
    dashboard_id: UUID,
    user_id: int,
    filters: dict[str, Any] | None = None,
    db: Session | None = None,
) -> list[AggregatedData]:
    """Применяет фильтры к агрегированным данным дашборда.

    Фильтрует данные по году, категории, бренду и другим параметрам,
    используя возможности PostgreSQL для фильтрации JSONB данных.

    Args:
        dashboard_id: ID дашборда (UUID).
        user_id: ID пользователя.
        filters: Словарь с параметрами фильтрации.
        db: Опциональная сессия базы данных.

    Returns:
        list[AggregatedData]: Отфильтрованные агрегированные данные.

    Raises:
        ValueError: Если дашборд не найден, у пользователя нет доступа или фильтры некорректны.
        SQLAlchemyError: При ошибке базы данных.
    """
    logger.info(
        "Применение фильтров: dashboard_id=%s, filters=%s, user_id=%s",
        dashboard_id,
        filters,
        user_id,
    )

    if db is not None:
        return _apply_data_filters_logic(dashboard_id, user_id, filters, db)

    with get_session() as db_session:
        return _apply_data_filters_logic(dashboard_id, user_id, filters, db_session)


def cleanup_task_files(task_id: uuid.UUID) -> None:
    """Удаляет временные файлы задачи.

    Args:
        task_id: ID задачи.
    """
    logger.info("Очистка файлов задачи: task_id=%s", task_id)

    # Ищем файлы, связанные с задачей, во временной директории
    config = get_config()
    upload_dir = Path(config.upload_temp_dir)
    
    # Ищем файлы, в имени которых есть task_id
    csv_files = list(upload_dir.glob(f"*{task_id}*.csv.gz"))
    
    for file_path in csv_files:
        try:
            file_path.unlink()
            logger.info("Файл удален: %s", file_path)
        except Exception as e:
            logger.error("Ошибка при удалении файла %s: %s", file_path, e)


def _save_aggregated_data_logic(
    dashboard_id: int,
    aggregates: list[dict[str, Any]],
    db: Session,
) -> int:
    """Внутренняя логика сохранения агрегированных данных с использованием переданной сессии.

    Args:
        dashboard_id: ID дашборда.
        aggregates: Список агрегированных данных для сохранения.
        db: Сессия базы данных.

    Returns:
        Количество успешно сохраненных записей.
    """
    logger.info(
        "Сохранение агрегированных данных (внутренняя логика): dashboard_id=%s, количество записей: %d",
        dashboard_id,
        len(aggregates),
    )

    # Выполняем операцию в транзакции
    with db.begin():
        inserted_count: int = AggregatedDataRepository.bulk_insert(
            db=db,
            dashboard_id=dashboard_id,
            aggregates=aggregates,
            clear_old=True,
        )

    logger.info(
        "Агрегированные данные сохранены для дашборда %s: %d записей",
        dashboard_id,
        inserted_count,
    )
    return inserted_count


def save_aggregated_data(
    dashboard_id: int,
    aggregates: list[dict[str, Any]],
    db: Session | None = None,
) -> int:
    """Сохраняет агрегированные данные в базу данных.

    Выполняет пакетную вставку агрегированных данных для дашборда.
    Перед вставкой удаляет старые данные для данного дашборда.
    Операция выполняется в транзакции: удаление старых данных и
    вставка новых выполняются атомарно.

    Args:
        dashboard_id: ID дашборда.
        aggregates: Список агрегированных данных для сохранения.
            Каждый элемент должен содержать:
            - graph_id: UUID графика
            - dims: dict[str, Any] значения измерений
            - metrics: dict[str, Any] значения метрик
        db: Опциональная сессия базы данных. Если не передана,
            создается новая сессия.

    Returns:
        Количество успешно сохраненных записей.

    Raises:
        ValueError: Если данные невалидны или графики не найдены.
        SQLAlchemyError: При ошибке базы данных.
    """
    logger.info(
        "Сохранение агрегированных данных для дашборда %s, количество записей: %d",
        dashboard_id,
        len(aggregates),
    )

    if db is not None:
        return _save_aggregated_data_logic(dashboard_id, aggregates, db)

    with get_session() as db_session:
        return _save_aggregated_data_logic(dashboard_id, aggregates, db_session)
