"""Сервис обработки данных.

Предоставляет бизнес-логику для загрузки, обработки и отслеживания статуса
обработки данных для дашбордов.
"""

import gzip
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import polars as pl
from sqlalchemy import Float, Integer
from sqlalchemy.orm import Session
from uuid import UUID

from mko_bi.config import config
from mko_bi.core.permissions import check_dashboard_access
from mko_bi.db.repositories.dashboard_repo import DashboardRepository
from mko_bi.db.session import SessionLocal
from mko_bi.models.data import (
    UploadResponse,
    ProcessingStatus,
    ProcessingResult,
    ProcessingConfig,
    AggregatedData,
)

logger = logging.getLogger(__name__)

# Хранилище статусов задач (в production использовать Redis или БД)
_task_statuses: dict[uuid.UUID, dict[str, Any]] = {}


def _validate_file(filename: str, file_content: bytes) -> None:
    """Валидирует загружаемый файл.

    Проверяет формат файла (.csv.gz) и размер (не более 100MB).

    Args:
        filename: Имя загружаемого файла.
        file_content: Содержимое файла в байтах.

    Raises:
        ValueError: Если файл не соответствует требованиям.
    """
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


def _save_uploaded_file(filename: str, file_content: bytes) -> Path:
    """Сохраняет загруженный файл во временную директорию.

    Args:
        filename: Имя файла.
        file_content: Содержимое файла.

    Returns:
        Path: Путь к сохраненному файлу.
    """
    upload_dir = Path(config.upload_temp_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Генерируем уникальное имя файла
    unique_filename = f"{uuid.uuid4()}_{filename}"
    file_path = upload_dir / unique_filename

    with open(file_path, "wb") as f:
        f.write(file_content)

    logger.info("Файл сохранен: %s", file_path)
    return file_path


def _process_csv_file(file_path: Path, processing_config: ProcessingConfig | None = None) -> dict[str, Any]:
    """Обрабатывает CSV файл с использованием Polars.

    Читает gzipped CSV файл, применяет трансформации и агрегации.

    Args:
        file_path: Путь к файлу.
        processing_config: Конфигурация обработки.

    Returns:
        dict: Результаты обработки.
    """
    logger.info("Начало обработки файла: %s", file_path)

    # Читаем gzipped CSV
    with gzip.open(file_path, "rt", encoding="utf-8") as f:
        # Сначала читаем в pandas, затем конвертируем в polars
        # (polars может читать CSV напрямую, но для gzipped нужен gzip)
        import pandas as pd
        df_pd = pd.read_csv(f)
        df = pl.from_pandas(df_pd)

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
            for filter_config in processing_config.filters:
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

        # Применяем группировку и агрегации
        if processing_config.groupby and processing_config.aggregations:
            group_cols = processing_config.groupby

            # Собираем агрегации
            agg_exprs = []
            for agg in processing_config.aggregations:
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
                df = df.group_by(group_cols).agg(agg_exprs)
                logger.info("Применена группировка: %s", group_cols)

        # Применяем трансформации
        if processing_config.transformations:
            for transform in processing_config.transformations:
                transform_type = transform.get("type")
                condition = transform.get("condition")

                if transform_type == "filter" and condition:
                    # Простая реализация фильтрации по условию
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

        result_data["processed_rows"] = df.shape[0]
        result_data["processed_columns"] = df.columns
        result_data["preview"] = df.head(10).to_dicts()
    else:
        result_data["processed_rows"] = df.shape[0]
        result_data["processed_columns"] = df.columns

    logger.info("Обработка завершена: %d строк", df.shape[0])
    return result_data


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

    # Проверка прав доступа
    local_session = False
    if db is None:
        db = SessionLocal()
        local_session = True

    try:
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
        file_path = _save_uploaded_file(filename, file_content)

        # Создание задачи
        task_id = uuid.uuid4()
        task_data = {
            "task_id": task_id,
            "filename": filename,
            "dashboard_id": dashboard_id,
            "status": "uploaded",
            "progress": 0,
            "message": "File uploaded successfully",
            "uploaded_at": datetime.now(),
            "started_at": None,
            "completed_at": None,
            "file_path": str(file_path),
            "user_id": user_id,
        }
        _task_statuses[task_id] = task_data

        logger.info(
            "Файл успешно загружен: task_id=%s, filename=%s", task_id, filename
        )

        return UploadResponse(
            task_id=task_id,
            filename=filename,
            dashboard_id=dashboard_id,
            status="uploaded",
            message="File uploaded successfully",
            uploaded_at=task_data["uploaded_at"],
        )

    except (ValueError, PermissionError):
        raise
    except Exception as e:
        logger.error("Ошибка при загрузке файла: %s", e)
        raise
    finally:
        if local_session:
            db.close()


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

    local_session = False
    if db is None:
        db = SessionLocal()
        local_session = True

    try:
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

        # Проверка существования задачи
        if task_id not in _task_statuses:
            logger.warning("Задача не найдена: task_id=%s", task_id)
            raise ValueError(f"Задача с id={task_id} не найдена")

        task_data = _task_statuses[task_id]

        # Проверка статуса задачи
        if task_data["status"] in ["processing", "completed"]:
            logger.warning(
                "Невозможно запустить обработку: задача уже %s", task_data["status"]
            )
            raise ValueError(
                f"Задача уже находится в статусе '{task_data['status']}'"
            )

        # Обновление статуса
        task_data["status"] = "processing"
        task_data["progress"] = 10
        task_data["message"] = "Processing started"
        task_data["started_at"] = datetime.now()

        logger.info("Обработка запущена: task_id=%s", task_id)

        # Выполнение обработки
        try:
            file_path = Path(task_data["file_path"])
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            # Обновление прогресса
            task_data["progress"] = 30

            # Обработка файла
            result_data = _process_csv_file(file_path, processing_config)

            # Обновление прогресса
            task_data["progress"] = 90

            # Сохранение результатов (в production - в БД)
            task_data["result"] = result_data
            task_data["processing_config"] = (
                processing_config.model_dump() if processing_config else None
            )

            # Завершение обработки
            task_data["status"] = "completed"
            task_data["progress"] = 100
            task_data["message"] = "Processing completed successfully"
            task_data["completed_at"] = datetime.now()

            logger.info(
                "Обработка завершена: task_id=%s, rows=%d",
                task_id,
                result_data.get("rows", 0),
            )

        except Exception as e:
            task_data["status"] = "failed"
            task_data["message"] = f"Processing failed: {str(e)}"
            task_data["completed_at"] = datetime.now()
            logger.error("Ошибка при обработке файла: task_id=%s, error=%s", task_id, e)
            raise

        return ProcessingStatus(
            task_id=task_data["task_id"],
            filename=task_data["filename"],
            dashboard_id=task_data["dashboard_id"],
            status=task_data["status"],
            progress=task_data["progress"],
            message=task_data["message"],
            started_at=task_data["started_at"],
            completed_at=task_data["completed_at"],
        )

    except (ValueError, PermissionError):
        raise
    except Exception as e:
        logger.error("Ошибка при запуске обработки: %s", e)
        raise
    finally:
        if local_session:
            db.close()


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

    local_session = False
    if db is None:
        db = SessionLocal()
        local_session = True

    try:
        # Проверка существования задачи
        if task_id not in _task_statuses:
            logger.warning("Задача не найдена: task_id=%s", task_id)
            raise ValueError(f"Задача с id={task_id} не найдена")

        task_data = _task_statuses[task_id]

        # Проверка прав доступа к дашборду
        has_access = check_dashboard_access(
            user_id=user_id,
            dashboard_id=task_data["dashboard_id"],
            required_permission="view",
            db=db,
        )
        if not has_access:
            logger.warning(
                "Нет прав на просмотр статуса: user_id=%d, dashboard_id=%d",
                user_id,
                task_data["dashboard_id"],
            )
            raise PermissionError("Недостаточно прав для просмотра статуса")

        logger.info("Статус получен: task_id=%s, status=%s", task_id, task_data["status"])

        return ProcessingStatus(
            task_id=task_data["task_id"],
            filename=task_data["filename"],
            dashboard_id=task_data["dashboard_id"],
            status=task_data["status"],
            progress=task_data["progress"],
            message=task_data["message"],
            started_at=task_data["started_at"],
            completed_at=task_data["completed_at"],
        )

    except (ValueError, PermissionError):
        raise
    except Exception as e:
        logger.error("Ошибка при получении статуса: %s", e)
        raise
    finally:
        if local_session:
            db.close()


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

    local_session = False
    if db is None:
        db = SessionLocal()
        local_session = True

    try:
        # Проверка существования задачи
        if task_id not in _task_statuses:
            logger.warning("Задача не найдена: task_id=%s", task_id)
            raise ValueError(f"Задача с id={task_id} не найдена")

        task_data = _task_statuses[task_id]

        # Проверка прав доступа
        has_access = check_dashboard_access(
            user_id=user_id,
            dashboard_id=task_data["dashboard_id"],
            required_permission="view",
            db=db,
        )
        if not has_access:
            logger.warning(
                "Нет прав на просмотр результата: user_id=%d, dashboard_id=%d",
                user_id,
                task_data["dashboard_id"],
            )
            raise PermissionError("Недостаточно прав для просмотра результата")

        # Проверка статуса
        if task_data["status"] != "completed":
            logger.warning(
                "Задача не завершена: task_id=%s, status=%s",
                task_id,
                task_data["status"],
            )
            raise ValueError(f"Задача не завершена (статус: {task_data['status']})")

        result_data = task_data.get("result", {})

        logger.info("Результат получен: task_id=%s", task_id)

        return ProcessingResult(
            success=True,
            task_id=task_id,
            dashboard_id=task_data["dashboard_id"],
            rows_processed=result_data.get("processed_rows", 0),
            message=task_data["message"],
            data=result_data,
        )

    except (ValueError, PermissionError):
        raise
    except Exception as e:
        logger.error("Ошибка при получении результата: %s", e)
        raise
    finally:
        if local_session:
            db.close()


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

    local_session = False
    if db is None:
        db = SessionLocal()
        local_session = True

    try:
        # Проверка существования дашборда и прав доступа
        from mko_bi.db.repositories.dashboard_repo import DashboardRepository

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
        from mko_bi.db.models import graphs as graphs_model
        from mko_bi.db.models import aggregated_data as aggregated_data_model

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
                graph_data.append(
                    {
                        "dims": agg.dims,
                        "metrics": agg.metrics,
                    }
                )

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

    except PermissionError:
        raise
    except ValueError:
        raise
    except Exception as e:
        logger.error(
            "Ошибка при получении агрегатов дашборда id=%s: %s",
            dashboard_id,
            e,
        )
        raise
    finally:
        if local_session:
            db.close()


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

    local_session = False
    if db is None:
        db = SessionLocal()
        local_session = True

    try:
        # Проверка существования дашборда и прав доступа
        from mko_bi.db.repositories.dashboard_repo import DashboardRepository

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
        from mko_bi.db.models import graphs as graphs_model
        from mko_bi.db.models import aggregated_data as aggregated_data_model

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
                graph_data.append(
                    {
                        "dims": agg.dims,
                        "metrics": agg.metrics,
                    }
                )

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

    except PermissionError:
        raise
    except ValueError:
        raise
    except Exception as e:
        logger.error(
            "Ошибка при получении данных для графиков дашборда id=%s: %s",
            dashboard_id,
            e,
        )
        raise
    finally:
        if local_session:
            db.close()


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

    local_session = False
    if db is None:
        db = SessionLocal()
        local_session = True

    try:
        # Проверка существования дашборда и прав доступа
        from mko_bi.db.repositories.dashboard_repo import DashboardRepository

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
        from mko_bi.db.models import graphs as graphs_model
        from mko_bi.db.models import aggregated_data as aggregated_data_model

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
            if filters and "filters" in filters and isinstance(filters["filters"], dict):
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
                graph_data.append(
                    {
                        "dims": agg.dims,
                        "metrics": agg.metrics,
                    }
                )

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

    except PermissionError:
        raise
    except ValueError:
        raise
    except Exception as e:
        logger.error(
            "Ошибка при применении фильтров к дашборду id=%s: %s",
            dashboard_id,
            e,
        )
        raise
    finally:
        if local_session:
            db.close()


def cleanup_task_files(task_id: uuid.UUID) -> None:
    """Удаляет временные файлы задачи.

    Args:
        task_id: ID задачи.
    """
    logger.info("Очистка файлов задачи: task_id=%s", task_id)

    if task_id in _task_statuses:
        task_data = _task_statuses[task_id]
        file_path = task_data.get("file_path")

        if file_path:
            try:
                path = Path(file_path)
                if path.exists():
                    path.unlink()
                    logger.info("Файл удален: %s", file_path)
            except Exception as e:
                logger.error("Ошибка при удалении файла %s: %s", file_path, e)

        # Удаление данных задачи
        del _task_statuses[task_id]
        logger.info("Данные задачи удалены: task_id=%s", task_id)
