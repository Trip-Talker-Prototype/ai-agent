from datetime import datetime
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from sqlalchemy import URL

timezone = ZoneInfo("Asia/Jakarta")


def build_connection_url(
    driver_name: str,
    username: str,
    password: str,
    host: str,
    port: str | int,
    database: str,
) -> URL:
    return URL.create(
        drivername=driver_name,
        username=username,
        password=password,
        host=host,
        port=port,
        database=database,
    )


def generate_time_now():
    return datetime.now(tz=timezone)


def generate_uuid() -> UUID:
    return uuid4()
