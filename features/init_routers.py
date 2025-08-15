from aiogram import Router
from .add_alliance import handlers as add_alliance_handlers
from .settings_alliance import handlers as settings_handlers

def setup_routers() -> Router:
    main_router = Router()
    main_router.include_router(add_alliance_handlers.router)
    main_router.include_router(settings_handlers.router)
    return main_router