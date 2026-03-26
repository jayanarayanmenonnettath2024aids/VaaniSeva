from typing import Any, Dict

REQUIRED_KEYS = ["customer_name", "mobile", "issue", "location", "issue_type"]


def empty_structure() -> Dict[str, str]:
    return {key: "" for key in REQUIRED_KEYS}


def validate_json(data: Any) -> Dict[str, str]:
    base = empty_structure()
    if not isinstance(data, dict):
        return base

    for key in REQUIRED_KEYS:
        value = data.get(key, "")
        if value is None:
            value = ""
        base[key] = str(value).strip()

    return base
