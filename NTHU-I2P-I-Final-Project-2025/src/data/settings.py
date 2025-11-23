import pygame as pg
import json
from src.utils import GameSettings
from src.utils.definition import Monster, Item


class Settings:
    _monsters_data: list[Monster]
    _items_data: list[Item]

    def __init__(self, monsters_data: list[Monster] | None = None, items_data: list[Item] | None = None):
        self._monsters_data = monsters_data if monsters_data else []
        self._items_data = items_data if items_data else []

    def update(self, dt: float):
        pass

    def draw(self, screen: pg.Surface):
        RECT = pg.Rect(50, 50, GameSettings.SCREEN_WIDTH - 100, GameSettings.SCREEN_HEIGHT - 100)
        pg.draw.rect(screen, (200, 200, 200), RECT)
        pass

    def to_dict(self) -> dict[str, object]:
        return {
            "monsters": list(self._monsters_data),
            "items": list(self._items_data)
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Settings":
        monsters = data.get("monsters") or []
        items = data.get("items") or []
        computer_monsters = data.get("computer_mostrers") or []
        bag = cls(monsters, items, computer_monsters)
        return bag