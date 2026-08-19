from typing import Annotated

from fastapi import Depends
from sqlalchemy.engine import Engine

from backend.core.config import Settings, get_settings
from backend.db.session import get_engine


SettingsDep = Annotated[Settings, Depends(get_settings)]
EngineDep = Annotated[Engine, Depends(get_engine)]

