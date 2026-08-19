from sqlalchemy import text
from sqlalchemy.engine import Engine


def rows(engine: Engine, sql: str, params: dict | None = None) -> list[dict]:
    with engine.connect() as connection:
        result = connection.execute(text(sql), params or {}).mappings()
        return [dict(item) for item in result]


def row(engine: Engine, sql: str, params: dict | None = None) -> dict | None:
    values = rows(engine, sql, params)
    return values[0] if values else None

