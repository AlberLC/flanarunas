from dataclasses import dataclass


@dataclass(frozen=True)
class Champion:
    id: int
    name: str
