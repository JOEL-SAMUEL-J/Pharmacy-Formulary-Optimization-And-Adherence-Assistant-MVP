from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "Pharmacy Formulary Optimization and Adherence Assistant API"
    app_env: str = "development"
    api_prefix: str = "/api/v1"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3306
    mysql_user: str = "pharmacy_app"
    mysql_password: str = ""
    mysql_database: str = "pharmacy_formulary"
    mysql_pool_size: int = 5
    mysql_max_overflow: int = 10

    generation_version: str = "mvp_v2.3"
    model_run_name: str = "mvp_v2_3_run_20260817T155422Z"
    model_path: Path = PROJECT_ROOT / "backend/model_artifacts/logistic_regression_pipeline.joblib"
    model_metadata_path: Path = PROJECT_ROOT / "backend/model_artifacts/model_selection.json"
    model_threshold: float = 0.405
    scoring_batch_size: int = 500
    prescriber_minimum_members: int = Field(default=5, ge=1, le=1000)
    prescriber_high_tier_threshold: int = Field(default=4, ge=1, le=6)
    prescriber_cost_burden_threshold: float = Field(default=0.50, ge=0, le=1)

    @field_validator("model_path", "model_metadata_path", mode="before")
    @classmethod
    def resolve_project_path(cls, value):
        path = Path(value)
        return path if path.is_absolute() else PROJECT_ROOT / path

    @property
    def database_url(self) -> str:
        from urllib.parse import quote_plus

        user = quote_plus(self.mysql_user)
        password = quote_plus(self.mysql_password)
        return (
            f"mysql+pymysql://{user}:{password}@{self.mysql_host}:"
            f"{self.mysql_port}/{self.mysql_database}?charset=utf8mb4"
        )

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
