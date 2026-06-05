from __future__ import annotations

import json


def render_json(package: dict) -> bytes:
    return json.dumps(package, indent=2, default=str).encode("utf-8")
