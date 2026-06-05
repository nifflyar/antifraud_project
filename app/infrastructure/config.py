from dataclasses import dataclass
import os
from pathlib import Path
from typing import Annotated
import yaml

from pydantic import SecretStr
from annotated_types import Gt, Lt, Ge, Le
from annotated_types import MinLen

from app.infrastructure.validators import HttpUrl


@dataclass
class PostgresConfig:
    host: str
    port: Annotated[int, Gt(0), Lt(65536)]
    user: str
    password: SecretStr
    db: str
    echo: bool = False
    pool_size: int = 100  # Увеличено с 30 для высокой нагрузки
    pool_timeout: int = 5  # Уменьшено для быстрого отказа
    pool_recycle: int = 600  # Переподключение каждые 10 минут
    max_overflow: int = 50  # Дополнительные соединения при пиках
    pool_pre_ping: bool = True
    echo_pool: bool = False

    def get_url(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password.get_secret_value()}@{self.host}:{self.port}/{self.db}"


@dataclass
class AuthConfig:
    secret_key: Annotated[SecretStr, MinLen(32)]
    algorithm: Annotated[str, MinLen(1)]
    access_token_expire_minutes: Annotated[int, Gt(0)]
    refresh_token_expire_days: Annotated[int, Gt(0)]
    admin_emails: list[str]


@dataclass
class TelemetryConfig:
    alloy_base: Annotated[SecretStr, HttpUrl()]
    export_metrics: bool = True
    export_traces: bool = True
    sentry_dsn: Annotated[SecretStr, HttpUrl()] | None = None
    sentry_traces_sample_rate: Annotated[float, Ge(0.0), Le(1.0)] = 1.0
    sentry_ca_certs: str | None = None


@dataclass
class MlConfig:
    url: Annotated[str, HttpUrl()]
    timeout: Annotated[int, Gt(0)] = 60


@dataclass
class Config:
    postgres: PostgresConfig
    auth: AuthConfig
    telemetry: TelemetryConfig
    ml: MlConfig
    environment: str = "development"


def load_config(file_name: str | None = None) -> Config:
    if file_name is None:
        file_name = os.environ.get("CONFIG_PATH", "config.yaml")

    file_path = Path(file_name)
    if not file_path.is_file():
        raise FileNotFoundError(f"Config file '{file_name}' not found")

    with open(file_path, 'r') as f:
        config_data = yaml.safe_load(f)

    pg_data = config_data['postgres']
    if isinstance(pg_data['password'], str):
        pg_data['password'] = SecretStr(pg_data['password'])
    config_data['postgres'] = PostgresConfig(**pg_data)

    auth_data = config_data['auth']
    if isinstance(auth_data['secret_key'], str):
        auth_data['secret_key'] = SecretStr(auth_data['secret_key'])
    config_data['auth'] = AuthConfig(**auth_data)

    tel_data = config_data['telemetry']
    if isinstance(tel_data['alloy_base'], str):
        tel_data['alloy_base'] = SecretStr(tel_data['alloy_base'])
    if tel_data.get('sentry_dsn') and isinstance(tel_data['sentry_dsn'], str):
        tel_data['sentry_dsn'] = SecretStr(tel_data['sentry_dsn'])
    config_data['telemetry'] = TelemetryConfig(**tel_data)

    config_data['ml'] = MlConfig(**config_data['ml'])

    return Config(**config_data)
