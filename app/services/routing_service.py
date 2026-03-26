from typing import Dict


ROUTING_MAP = {
    "Road": {"department": "PWD", "sla_hours": 48},
    "Water": {"department": "Municipality", "sla_hours": 24},
    "Electricity": {"department": "EB", "sla_hours": 6},
    "Garbage": {"department": "Sanitation", "sla_hours": 24},
    "Street Light": {"department": "PWD", "sla_hours": 48},
}


def get_department(issue_type: str) -> Dict[str, int | str]:
    normalized = (issue_type or "").strip()
    if normalized in ROUTING_MAP:
        return ROUTING_MAP[normalized]

    return {"department": "General Department", "sla_hours": 24}
