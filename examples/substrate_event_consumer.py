"""Example Cognitive Substrate event consumer."""

from __future__ import annotations

import json

from federalspendai.config import get_settings


def load_recent_events(limit: int = 10) -> list[dict]:
    event_dir = get_settings().data_dir / "events"
    if not event_dir.exists():
        return []
    files = sorted(event_dir.glob("*.json"), reverse=True)[:limit]
    return [json.loads(path.read_text()) for path in files]


if __name__ == "__main__":
    for event in load_recent_events():
        print(f"{event['event_type']}: {list(event['payload'].keys())}")
