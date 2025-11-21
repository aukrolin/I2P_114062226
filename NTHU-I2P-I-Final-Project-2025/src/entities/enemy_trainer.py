from __future__ import annotations
import pygame
from enum import Enum
from dataclasses import dataclass
from typing import override

from .entity import Entity
from src.sprites import Sprite
from src.entities.player import Player
from src.core import GameManager
from src.core.services import input_manager, scene_manager
from src.utils import GameSettings, Direction, Position, PositionCamera


class EnemyTrainerClassification(Enum):
    STATIONARY = "stationary"

@dataclass
class IdleMovement:
    def update(self, enemy: "EnemyTrainer", dt: float) -> None:
        return

class EnemyTrainer(Entity):
    classification: EnemyTrainerClassification
    max_tiles: int | None
    _movement: IdleMovement
    warning_sign: Sprite
    detected: bool
    LOS_direction: Direction

    @override
    def __init__(
        self,
        x: float,
        y: float,
        game_manager: GameManager,
        classification: EnemyTrainerClassification = EnemyTrainerClassification.STATIONARY,
        max_tiles: int | None = 2,
        facing: Direction | None = None,
    ) -> None:
        super().__init__(x, y, game_manager)
        self.classification = classification
        self.max_tiles = max_tiles if max_tiles is not None else 0
        if classification == EnemyTrainerClassification.STATIONARY:
            self._movement = IdleMovement()
            if facing is None:
                raise ValueError("Idle EnemyTrainer requires a 'facing' Direction at instantiation")
            self._set_direction(facing)
        else:
            raise ValueError("Invalid classification")
        self.warning_sign = Sprite("exclamation.png", (GameSettings.TILE_SIZE // 2, GameSettings.TILE_SIZE // 2))
        self.warning_sign.update_pos(Position(x + GameSettings.TILE_SIZE // 4, y - GameSettings.TILE_SIZE // 2))
        self.detected = False

    @override
    def update(self, dt: float) -> None:
        self._movement.update(self, dt)
        self._has_LOS_to_player()
        if self.detected and input_manager.key_pressed(pygame.K_SPACE):
            scene_manager.change_scene("battle")
        self.animation.update_pos(self.position)

    @override
    def draw(self, screen: pygame.Surface, camera: PositionCamera) -> None:
        super().draw(screen, camera)
        if self.detected:
            self.warning_sign.draw(screen, camera)
        if GameSettings.DRAW_LOS:
            LOS_rect = self._get_LOS_rect()
            if LOS_rect is not None:
                pygame.draw.rect(screen, (255, 255, 0), camera.transform_rect(LOS_rect), 1)

    def _set_direction(self, direction: Direction) -> None:
        self.direction = direction
        if direction == Direction.RIGHT:
            self.animation.switch("right")
        elif direction == Direction.LEFT:
            self.animation.switch("left")
        elif direction == Direction.DOWN:
            self.animation.switch("down")
        else:
            self.animation.switch("up")
        self.LOS_direction = self.direction

    def _get_LOS_rect(self) -> pygame.Rect | None:
        '''
        TODO: Create hitbox to detect line of sight of the enemies towards the player
        '''
        if self.LOS_direction == Direction.UP:
            left = self.position.x
            top = self.position.y - GameSettings.TILE_SIZE * self.max_tiles
            width = GameSettings.TILE_SIZE
            height = GameSettings.TILE_SIZE * self.max_tiles 
        elif self.LOS_direction == Direction.DOWN:
            left = self.position.x
            top = self.position.y + GameSettings.TILE_SIZE
            width = GameSettings.TILE_SIZE
            height = GameSettings.TILE_SIZE * self.max_tiles
        elif self.LOS_direction == Direction.LEFT:
            left = self.position.x - GameSettings.TILE_SIZE * self.max_tiles
            top = self.position.y
            width = GameSettings.TILE_SIZE * self.max_tiles
            height = GameSettings.TILE_SIZE
        elif self.LOS_direction == Direction.RIGHT:
            left = self.position.x + GameSettings.TILE_SIZE
            top = self.position.y
            width = GameSettings.TILE_SIZE * self.max_tiles
            height = GameSettings.TILE_SIZE
        else:
            raise ValueError("Invalid LOS direction")
        LOSrect = pygame.Rect(left, top, width, height)
        return LOSrect


    def _has_LOS_to_player(self) -> None:
        player: Player | None = self.game_manager.player
        if player is None:
            self.detected = False
            raise ValueError("Player not found in game manager")
        LOS_rect = self._get_LOS_rect()
        if LOS_rect is None:
            self.detected = False
            raise ValueError("LOS rect could not be created")
        if LOS_rect.colliderect(player.hitbox):
            self.detected = True
            # print("Player detected by EnemyTrainer")
        else:            
            self.detected = False
        '''
        TODO: Implement line of sight detection
        If it's detected, set self.detected to True
        '''

    @classmethod
    @override
    def from_dict(cls, data: dict, game_manager: GameManager) -> "EnemyTrainer":
        classification = EnemyTrainerClassification(data.get("classification", "stationary"))
        max_tiles = data.get("max_tiles")
        facing_val = data.get("facing")
        facing: Direction | None = None
        if facing_val is not None:
            if isinstance(facing_val, str):
                facing = Direction[facing_val]
            elif isinstance(facing_val, Direction):
                facing = facing_val
        if facing is None and classification == EnemyTrainerClassification.STATIONARY:
            facing = Direction.DOWN
        return cls(
            data["x"] * GameSettings.TILE_SIZE,
            data["y"] * GameSettings.TILE_SIZE,
            game_manager,
            classification,
            max_tiles,
            facing,
        )

    @override
    def to_dict(self) -> dict[str, object]:
        base: dict[str, object] = super().to_dict()
        base["classification"] = self.classification.value
        base["facing"] = self.direction.name
        base["max_tiles"] = self.max_tiles
        return base