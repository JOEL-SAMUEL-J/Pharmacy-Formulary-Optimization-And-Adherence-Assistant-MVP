from sqlalchemy import text
from sqlalchemy.engine import Engine


def database_health(engine: Engine) -> dict:
    with engine.connect() as connection:
        value = connection.execute(text("SELECT 1")).scalar_one()
    return {"connected": value == 1}

