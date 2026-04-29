from __future__ import annotations

import json
from typing import Callable, Iterable


def respond_json(start_response: Callable, status: str, payload: dict) -> Iterable[bytes]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = [
        ("Content-Type", "application/json; charset=utf-8"),
        ("Content-Length", str(len(body))),
    ]
    start_response(status, headers)
    return [body]

