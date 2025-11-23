import pygame as pg
import json
from src.utils import GameSettings
from src.utils.definition import Monster, Item


class Bag:
    _monsters_data: list[Monster]
    _items_data: list[Item]

    def __init__(self, monsters_data: list[Monster] | None = None, items_data: list[Item] | None = None, computer_monsters_data: list[Monster] | None = None):
        self._monsters_data = monsters_data if monsters_data else []
        self._items_data = items_data if items_data else []
        self.monsters_len = len(self._monsters_data)
        self.computer_monsters_data = computer_monsters_data if computer_monsters_data else []
    def update(self, dt: float):
        pass
    
    def get_monsters(self) -> list[Monster]:
        return self._monsters_data
    def get_items(self) -> list[Item]:
        return self._items_data

    def __repr__(self):
        return f"Bag(monsters={self._monsters_data}, items={self._items_data})"

    def to_dict(self) -> dict[str, object]:
        return {
            "monsters": list(self._monsters_data),
            "items": list(self._items_data),
            "computer_mostrers": list(self.computer_monsters_data) 
        }

    def add_monster(self, monster: Monster) -> None:
        MAX_MONSTERS_IN_BAG = GameSettings.MAX_MONSTERS_IN_BAG
        self.monsters_len = len(self._monsters_data)
        if self.monsters_len >= MAX_MONSTERS_IN_BAG:
            self.computer_monsters_data.append(monster)
            return
        else :
            self._monsters_data.append(monster)

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Bag":
        monsters = data.get("monsters") or []
        items = data.get("items") or []
        computer_monsters = data.get("computer_mostrers") or []
        bag = cls(monsters, items, computer_monsters)
        return bag