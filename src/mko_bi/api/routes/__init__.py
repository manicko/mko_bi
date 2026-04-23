# API routes
from mko_bi.api.routes.auth import router as auth_router
from mko_bi.api.routes.users import router as users_router
from mko_bi.api.routes.dashboards import router as dashboards_router
from mko_bi.api.routes.upload import router as upload_router

__all__ = ["auth_router", "users_router", "dashboards_router", "upload_router"]
