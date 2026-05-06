"""Оркестрация пайплайна обработки данных.

Содержит класс DataPipeline, который управляет последовательностью
трансформации, агрегации, сохранения и обновления статусов.
"""

import logging
from uuid import UUID

import polars as pl
from sqlalchemy.ext.asyncio import AsyncSession

from mko_bi.data.processing.transformations import (
    apply_transformations,
    aggregate_data,
)
from mko_bi.data.storage.manager import StorageManager
from mko_bi.models.enums import ProcessingStatus, UploadMode
from mko_bi.models.processing_logs import ProcessingLogRead
from mko_bi.services.processing_config_service import get_by_dashboard_id

logger = logging.getLogger(__name__)


class DataPipeline:
    """Оркестрация обработки данных.

    Управляет последовательностью шагов: трансформация,
    агрегация, сохранение и обновление статуса.

    Attributes:
        storage_manager: Менеджер для сохранения агрегированных данных.
    """

    def __init__(self, storage_manager: StorageManager) -> None:
        """Инициализация пайплайна.

        Args:
            storage_manager: Экземпляр менеджера хранения данных.
        """
        self.storage_manager = storage_manager
        logger.debug("DataPipeline инициализирован")

    async def run(
        self,
        df: pl.DataFrame,
        dashboard_id: UUID,
        mode: UploadMode,
        db: AsyncSession,
    ) -> ProcessingLogRead:
        """Запускает пайплайн обработки данных.

        Args:
            df: Исходный DataFrame с данными.
            dashboard_id: Идентификатор дашборда.
            mode: Режим загрузки (overwrite/append).
            db: Асинхронная сессия БД.

        Returns:
            ProcessingLogRead: Результат выполнения с статусом.
        """
        from mko_bi.services.processing_log_service import create_log, update_log_status
        from mko_bi.db.repositories.graph_repo import GraphRepository

        log_entry = None
        try:
            logger.info(
                "Запуск пайплайна для dashboard_id=%s, mode=%s",
                dashboard_id,
                mode,
            )

            # Создаем запись в логе
            log_entry = await create_log(
                dashboard_id=dashboard_id,
                status=ProcessingStatus.STARTED,
                db=db,
            )

            # Шаг 1: Получаем конфиг и трансформируем
            logger.info("Шаг 1: Трансформация данных")
            config_response = await get_by_dashboard_id(dashboard_id, db)
            config = config_response.settings if config_response else {}
            
            transformed_df = apply_transformations(df, config)
            logger.info("Трансформация завершена: %d строк", transformed_df.shape[0])

            # Шаг 2: Получаем графики и агрегируем
            logger.info("Шаг 2: Агрегация данных")
            graphs = await GraphRepository.get_by_dashboard(dashboard_id, db)
            graph_configs = [
                {
                    "dimensions": g.dimensions,
                    "metrics": g.metrics,
                }
                for g in graphs
            ]
            
            aggregates = aggregate_data(transformed_df, graph_configs)
            
            # Добавляем graph_id к каждому агрегату
            for agg, g in zip(aggregates, graphs, strict=False):
                agg["graph_id"] = g.id
            
            logger.info("Агрегация завершена: %d записей", len(aggregates))

            # Шаг 3: Сохранение
            logger.info("Шаг 3: Сохранение данных")
            clear_old = mode == UploadMode.OVERWRITE
            await self.storage_manager.save_aggregates(
                dashboard_id=dashboard_id,
                aggregates=aggregates,
                clear_old=clear_old,
            )
            logger.info("Сохранение завершено")

            # Обновляем статус лога
            updated_log = await update_log_status(
                log_id=log_entry.id,
                status=ProcessingStatus.COMPLETED,
                db=db,
            )
            logger.info("Пайплайн успешно завершен")
            return updated_log

        except Exception as e:
            logger.error("Ошибка в пайплайне: %s", e)
            if log_entry:
                await update_log_status(
                    log_id=log_entry.id,
                    status=ProcessingStatus.FAILED,
                    db=db,
                    message=str(e),
                )
            raise

    async def _update_status(
        self,
        log_id: UUID,
        status: ProcessingStatus,
        db: AsyncSession,
        message: str | None = None,
    ) -> None:
        """Обновляет статус в логе обработки.

        Args:
            log_id: Идентификатор записи в логе.
            status: Новый статус.
            db: Асинхронная сессия БД.
            message: Опциональное сообщение об ошибке.
        """
        from mko_bi.services.processing_log_service import update_log_status

        logger.debug("Обновление статуса log_id=%s: %s", log_id, status)
        await update_log_status(
            log_id=log_id,
            status=status,
            db=db,
            message=message,
        )
