from threading import Lock
from typing import Any, List


class RoundRobinBalancer:
    def __init__(self, list_of_accounts: List[Any]):
        self._items = list_of_accounts or []
        self._index = 0
        self._lock = Lock()

    def get_next(self) -> Any:
        if not self._items:
            raise ValueError("No accounts/keys configured for round robin balancer")

        with self._lock:
            item = self._items[self._index]
            self._index = (self._index + 1) % len(self._items)
            return item
