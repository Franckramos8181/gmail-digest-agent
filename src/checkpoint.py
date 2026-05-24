import json
from pathlib import Path


class CheckpointStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._ids: set[str] = set()
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            self._ids = set(data.get("processed_message_ids", []))
        except (json.JSONDecodeError, OSError):
            self._ids = set()

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"processed_message_ids": sorted(self._ids)[-5000:]}
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def is_processed(self, message_id: str) -> bool:
        return message_id in self._ids

    def mark_processed(self, message_ids: list[str]) -> None:
        self._ids.update(message_ids)
