from dataclasses import dataclass


@dataclass
class Event:
    type: str
    source: str
    payload: dict | str | bytes

    @staticmethod
    def from_dict(d: dict):
        return Event(
            type=d["type"],
            source=d.get("source", ""),
            payload=d.get("payload", {})
        )
