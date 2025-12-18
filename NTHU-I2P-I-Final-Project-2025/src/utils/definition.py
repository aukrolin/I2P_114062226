from pygame import Rect
from .settings import GameSettings
from dataclasses import dataclass
from enum import Enum
from typing import overload, TypedDict, Protocol, Tuple

MouseBtn = int
Key = int

Direction = Enum('Direction', ['UP', 'DOWN', 'LEFT', 'RIGHT', 'NONE'])

@dataclass
class Position:
    x: float
    y: float
    
    def copy(self):
        return Position(self.x, self.y)
        
    def distance_to(self, other: "Position") -> float:
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5
        
@dataclass
class PositionCamera:
    x: int
    y: int
    
    def copy(self):
        return PositionCamera(self.x, self.y)
        
    def to_tuple(self) -> tuple[int, int]:
        return (self.x, self.y)
        
    def transform_position(self, position: Position) -> tuple[int, int]:
        return (int(position.x) - self.x, int(position.y) - self.y)
        
    def transform_position_as_position(self, position: Position) -> Position:
        return Position(int(position.x) - self.x, int(position.y) - self.y)
        
    def transform_rect(self, rect: Rect) -> Rect:
        return Rect(rect.x - self.x, rect.y - self.y, rect.width, rect.height)

@dataclass
class Teleport:
    pos: Position
    destination: str
    
    @overload
    def __init__(self, x: int, y: int, destination: str, spawnx: int, spawny: int) -> None: ...
    @overload
    def __init__(self, pos: Position, destination: str, spawnx: int, spawny: int) -> None: ...

    def __init__(self, *args, **kwargs):
        if isinstance(args[0], Position):
            self.pos = args[0]
            self.destination = args[1]
            self.spawnx = args[2]
            self.spawny = args[3]
        else:
            x, y, dest, spawnx, spawny = args
            self.pos = Position(x, y)
            self.destination = dest
            self.spawnx = spawnx
            self.spawny = spawny
    
    def to_dict(self):
        return {
            "x": self.pos.x // GameSettings.TILE_SIZE,
            "y": self.pos.y // GameSettings.TILE_SIZE,
            "destination": self.destination,
            "spawnx": self.spawnx,
            "spawny": self.spawny
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(data["x"] * GameSettings.TILE_SIZE, data["y"] * GameSettings.TILE_SIZE, data["destination"], data['spawnx'], data['spawny'])
    
class Monster(TypedDict, total=False):
    """寶可夢資料結構"""
    name: str
    hp: int
    max_hp: int
    level: int
    sprite_path: str
    # 新增欄位（可選）
    element: Tuple[str, str | None]  # 屬性類型 (最多 2 個屬性)
    base_hp: int          # 基礎 HP
    attack: int           # 攻擊力 (物理攻擊)
    defense: int          # 防禦力 (物理防禦)
    sp_attack: int        # 特殊攻擊
    sp_defense: int       # 特殊防禦
    speed: int            # 速度
    attack_boost: int     # 攻擊力增益 (藥水效果，預設 0)
    defense_boost: int    # 防禦力增益 (藥水效果，預設 0)
    moves: list[dict]     # 招式列表
    can_evolve: bool      # 是否可進化
    evolution_item: str | None  # 進化所需道具 (例如 "Water Stone")
    evolution_target: str | None  # 進化後的寶可夢名稱

class Item(TypedDict, total=False):
    """物品資料結構"""
    name: str
    count: int
    sprite_path: str
    # 新增欄位（可選）
    price: int            # 物品價格 (商店物品需要)
    effect: str           # 物品效果類型 (heal, attack_boost, defense_boost, evolution)
    value: int            # 效果數值 (恢復量/增益量)
    target: list[str] | None  # 進化石目標寶可夢列表