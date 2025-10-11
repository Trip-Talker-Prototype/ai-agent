from uuid import UUID, uuid4
from datetime import datetime
from zoneinfo import ZoneInfo


timezone = ZoneInfo("Asia/Jakarta")

def generate_uuid() -> UUID:
    return uuid4()

def generate_time_now():
    return datetime.now(tz=timezone)