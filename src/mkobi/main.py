"""Main FastAPI application file.

Creates and configures the FastAPI application using factory pattern.
"""

from mkobi.app import create_app

# Create application instance via factory
app = create_app()
