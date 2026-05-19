from datetime import datetime

VALID_ROLES = {"client", "psychologist", "admin"}
PUBLIC_ROLES = {"client", "psychologist"}
PSYCHOLOGIST_ONLY_PROFILE_FIELDS = {"full_name", "education"}
CLIENT_ONLY_PROFILE_FIELDS = {"about"}


def normalize_role(role: str) -> str:
    normalized = role.strip().lower()
    if normalized not in VALID_ROLES:
        raise ValueError("Недопустимая роль пользователя")
    return normalized


def ensure_public_role(role: str) -> None:
    if role not in PUBLIC_ROLES:
        raise ValueError("Через регистрацию можно создать только клиента или психолога")


def ensure_profile_payload_allowed(role: str, fields: set[str]) -> None:
    if role == "client" and fields & PSYCHOLOGIST_ONLY_PROFILE_FIELDS:
        raise ValueError("Клиент не может заполнять поля профиля психолога")
    if role == "psychologist" and fields & CLIENT_ONLY_PROFILE_FIELDS:
        raise ValueError("Психолог не может заполнять клиентское описание о себе")
    if role == "admin" and fields:
        raise ValueError("Профиль администратора не содержит клиентских или психологических данных")


def validate_slot_window(start_at: datetime, end_at: datetime) -> None:
    if end_at <= start_at:
        raise ValueError("Время окончания должно быть позже времени начала")


def windows_overlap(
    first_start: datetime,
    first_end: datetime,
    second_start: datetime,
    second_end: datetime,
) -> bool:
    return first_start < second_end and first_end > second_start
