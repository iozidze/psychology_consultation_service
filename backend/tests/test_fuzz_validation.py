import random
import string
from datetime import datetime, timedelta

import pytest

from app.validators import (
    VALID_ROLES,
    ensure_profile_payload_allowed,
    normalize_role,
    validate_slot_window,
    windows_overlap,
)


def random_text(max_length=32):
    alphabet = string.ascii_letters + string.digits + string.punctuation + " абвгдеёжз"
    return "".join(random.choice(alphabet) for _ in range(random.randint(0, max_length)))


def test_fuzz_roles_reject_unknown_values():
    for _ in range(500):
        candidate = random_text()
        if candidate.strip().lower() in VALID_ROLES:
            assert normalize_role(candidate) in VALID_ROLES
        else:
            with pytest.raises(ValueError):
                normalize_role(candidate)


def test_fuzz_profile_role_boundaries():
    all_fields = ["full_name", "specialization", "education", "about"]
    for _ in range(250):
        fields = set(random.sample(all_fields, random.randint(0, len(all_fields))))
        if fields & {"full_name", "education"}:
            with pytest.raises(ValueError):
                ensure_profile_payload_allowed("client", fields)
        else:
            ensure_profile_payload_allowed("client", fields)


def test_fuzz_slot_window_validation_and_overlap():
    base = datetime(2026, 1, 1, 10, 0)
    for _ in range(250):
        start = base + timedelta(minutes=random.randint(-600, 600))
        end = base + timedelta(minutes=random.randint(-600, 600))
        if end <= start:
            with pytest.raises(ValueError):
                validate_slot_window(start, end)
        else:
            validate_slot_window(start, end)
            assert windows_overlap(start, end, start + timedelta(minutes=1), end + timedelta(minutes=1))
