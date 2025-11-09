from __future__ import annotations
import pygame as pg
from .entity import Entity
from src.core.services import input_manager
from src.utils import Position, PositionCamera, GameSettings, Logger
from src.core import GameManager
from math import hypot
from typing import override

class Player(Entity):
    speed: float = 4.0 * GameSettings.TILE_SIZE
    game_manager: GameManager

    def __init__(self, x: float, y: float, game_manager: GameManager) -> None:
        super().__init__(x, y, game_manager)

    @override
    def update(self, dt: float) -> None:
        dis = Position(0, 0)
        '''
        [TODO HACKATHON 2]
        Calculate the distance change, and then normalize the distance
        
        [TODO HACKATHON 4]
        Check if there is collision, if so try to make the movement smooth
        Hint #1 : use entity.py _snap_to_grid function or create a similar function
        Hint #2 : Beware of glitchy teleportation, you must do
                    1. Update X
                    2. If collide, snap to grid
                    3. Update Y
                    4. If collide, snap to grid
                  instead of update both x, y, then snap to grid
        
        if input_manager.key_down(pg.K_LEFT) or input_manager.key_down(pg.K_a):
            dis.x -= ...
        if input_manager.key_down(pg.K_RIGHT) or input_manager.key_down(pg.K_d):
            dis.x += ...
        if input_manager.key_down(pg.K_UP) or input_manager.key_down(pg.K_w):
            dis.y -= ...
        if input_manager.key_down(pg.K_DOWN) or input_manager.key_down(pg.K_s):
            dis.y += ...
        
        self.position = ...
        '''
        if input_manager.key_down(pg.K_w) or input_manager.key_down(pg.K_UP):
            dis.y -= 1
        if input_manager.key_down(pg.K_s) or input_manager.key_down(pg.K_DOWN):
            dis.y += 1
        if input_manager.key_down(pg.K_a) or input_manager.key_down(pg.K_LEFT):
            dis.x -= 1
        if input_manager.key_down(pg.K_d) or input_manager.key_down(pg.K_RIGHT):
            dis.x += 1
        length = hypot(dis.x, dis.y)
        if length != 0:
            dis.x /= length
            dis.y /= length
            pass
        
        def check_teleport_and_switch():
            tp = self.game_manager.current_map.check_teleport(self.position)
            if tp:
                Logger.info(f"Teleporting to {tp.destination}")
                dest = tp.destination
                self.game_manager.switch_map(dest)
                return True
            return False

        nx = self.position.x + dis.x * self.speed * dt
        if not self.check_collision(pg.Rect(nx,self.position.y,GameSettings.TILE_SIZE,GameSettings.TILE_SIZE)):
            self.position.x = nx
        else:
            if not check_teleport_and_switch():
                self.position.x = self._snap_to_grid(self.position.x)
        
        ny = self.position.y + dis.y * self.speed * dt
        if not self.check_collision(pg.Rect(self.position.x,ny,GameSettings.TILE_SIZE,GameSettings.TILE_SIZE)):
            self.position.y = ny
        else :
            if not check_teleport_and_switch():
                self.position.y = self._snap_to_grid(self.position.y)


        super().update(dt)

    def check_collision(self, rect: pg.Rect) -> bool:
        return self.game_manager.check_collision(rect) | self.game_manager.current_map.check_collision(rect)

    @override
    def draw(self, screen: pg.Surface, camera: PositionCamera) -> None:
        super().draw(screen, camera)
        
    @override
    def to_dict(self) -> dict[str, object]:
        return super().to_dict()
    
    @property
    def hitbox(self) -> pg.Rect:
        return super().hitbox

    @property
    @override
    def camera(self) -> PositionCamera:
        return PositionCamera(int(self.position.x) + GameSettings.TILE_SIZE // 2 - GameSettings.SCREEN_WIDTH // 2, int(self.position.y) + GameSettings.TILE_SIZE // 2 - GameSettings.SCREEN_HEIGHT // 2)
            
    @classmethod
    @override
    def from_dict(cls, data: dict[str, object], game_manager: GameManager) -> Player:
        return cls(data["x"] * GameSettings.TILE_SIZE, data["y"] * GameSettings.TILE_SIZE, game_manager)

