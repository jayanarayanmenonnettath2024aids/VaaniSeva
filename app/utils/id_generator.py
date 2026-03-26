import random
import string


def generate_ticket_id() -> str:
    suffix = "".join(random.choices(string.digits, k=6))
    return f"TKT-{suffix}"
