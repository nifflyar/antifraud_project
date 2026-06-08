from datetime import UTC, datetime, timedelta, timezone


ASTANA_TZ = timezone(timedelta(hours=5), name="GMT+5")
ASTANA_TZ_LABEL = "Астана (GMT+5)"


def to_astana_datetime(value: datetime | None, *, naive: bool = False) -> datetime | None:
    if value is None:
        return None

    aware_value = value if value.tzinfo is not None else value.replace(tzinfo=UTC)
    astana_value = aware_value.astimezone(ASTANA_TZ)
    return astana_value.replace(tzinfo=None) if naive else astana_value


def astana_now() -> datetime:
    return datetime.now(UTC).astimezone(ASTANA_TZ)


def format_astana_datetime(value: datetime | None, *, seconds: bool = False) -> str:
    astana_value = to_astana_datetime(value, naive=True)
    if astana_value is None:
        return "—"
    return astana_value.strftime("%d.%m.%Y %H:%M:%S" if seconds else "%d.%m.%Y %H:%M")


def astana_filename_timestamp() -> str:
    return astana_now().strftime("%Y%m%d_%H%M")
