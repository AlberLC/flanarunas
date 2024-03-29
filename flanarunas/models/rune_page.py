from dataclasses import dataclass
from typing import Any

from flanautils import FlanaBase


@dataclass(unsafe_hash=True)
class RunePage(FlanaBase):
    isActive: bool
    _name: str
    order: int
    primaryStyleId: int
    subStyleId: int
    selectedPerkIds: list[int]

    def __init__(self, isActive=False, name='', order=None, primaryStyleId=None, subStyleId=None, selectedPerkIds=None):
        self.isActive = isActive
        self.name = name
        self.order = order
        self.primaryStyleId = primaryStyleId
        self.subStyleId = subStyleId
        self.selectedPerkIds = selectedPerkIds or []

    @staticmethod
    def _format_name(rune_page_name: str) -> str:
        if rune_page_name.lower().startswith('f ') or rune_page_name.lower().startswith('f:'):
            rune_page_name = rune_page_name[2:].strip()

        return f'F: {rune_page_name}'

    def _json_repr(self) -> Any:
        return {k.strip('_'): v for k, v in vars(self).items()}

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, text: str):
        self._name = self._format_name(text)
