from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from backend.core.config import get_settings


@lru_cache
def get_engine() -> Engine:
    settings = get_settings()
    return create_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_recycle=1800,
        pool_size=settings.mysql_pool_size,
        max_overflow=settings.mysql_max_overflow,
        future=True,
    )


def dispose_engine() -> None:
    if get_engine.cache_info().currsize:
        get_engine().dispose()
        get_engine.cache_clear()

