"""Atomic local checkpoint files and append-only balance observations."""
import json
import logging
import os
from pathlib import Path


class RunStorage:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.checkpoints = self.directory / "checkpoints"
        self.checkpoints.mkdir(parents=True, exist_ok=True)

    def save(self, room):
        path = self.checkpoints / (room["code"] + ".json")
        temporary = path.with_suffix(".tmp")
        with temporary.open("w", encoding="utf-8") as stream:
            json.dump({"version": 1, "room": room}, stream, ensure_ascii=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)

    def load(self):
        rooms = []
        for path in self.checkpoints.glob("*.json"):
            try:
                document = json.loads(path.read_text(encoding="utf-8"))
                room = document["room"]
                if document["version"] != 1 or not room["players"] or not room["checkpoint"]:
                    raise ValueError("Unsupported or empty checkpoint")
                if room["code"] != path.stem or not all(c in "ABCDEFGHJKLMNPQRSTUVWXYZ23456789" for c in room["code"]):
                    raise ValueError("Invalid room code")
                rooms.append(room)
            except (ValueError, KeyError, TypeError, OSError):
                logging.exception("Could not load checkpoint %s; file preserved", path.name)
        return rooms

    def delete(self, code):
        (self.checkpoints / (code + ".json")).unlink(missing_ok=True)

    def record(self, report):
        with (self.directory / "balance.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(report, ensure_ascii=False) + "\n")
