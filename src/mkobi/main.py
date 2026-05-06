"""Главный файл приложения FastAPI.

Создает и конфигурирует приложение FastAPI через factory pattern.
"""

from mkobi.app import create_app

# Создаем экземпляр приложения через factory
app = create_app()
