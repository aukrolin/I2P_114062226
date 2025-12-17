from __future__ import annotations
import pygame as pg
from .entity import Entity
from src.core.services import input_manager
from src.utils import Position, PositionCamera,Direction, GameSettings, Logger
from src.core import GameManager
from math import hypot
from typing import override

class Player(Entity):
    speed: float = 4.0 * GameSettings.TILE_SIZE
    game_manager: GameManager



    def __init__(self, x: float, y: float, game_manager: GameManager) -> None:
        self.paused = False
        super().__init__(x, y, game_manager)
        self.cur = None
        self.prev = None


    @override
    def update(self, dt: float) -> None:
        # 更新移动锁定计时器
        if self.movement_lock_timer > 0:
            self.movement_lock_timer -= dt
            super().update(dt)
            return  # 锁定期间不允许移动
        
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
        self.updated = False
        
        if self.paused:
            super().update(dt)
            return  # paused, do nothing
        # print('doing')
        if input_manager.key_down(pg.K_w) or input_manager.key_down(pg.K_UP):
            dis.y -= 1
            self.animation.switch("up")
            self.direction = Direction.UP
        if input_manager.key_down(pg.K_s) or input_manager.key_down(pg.K_DOWN):
            dis.y += 1
            self.animation.switch("down")
            self.direction = Direction.DOWN
        if input_manager.key_down(pg.K_a) or input_manager.key_down(pg.K_LEFT):
            dis.x -= 1
            self.animation.switch("left")
            self.direction = Direction.LEFT
        if input_manager.key_down(pg.K_d) or input_manager.key_down(pg.K_RIGHT):
            dis.x += 1
            self.animation.switch("right")
            self.direction = Direction.RIGHT
        if dis.x == 0 and dis.y == 0:
            self.animation.stop()
        else :
            self.animation.re_play(dt)
        
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

                self.game_manager.switch_map(dest, tp.spawnx, tp.spawny)
                return True
            return False

        def update_position(dis: Position, dt: float):
            nx = self.position.x + dis.x * self.speed * dt
            ny = self.position.y + dis.y * self.speed * dt
            if dis.x or dis.y: 
                self.updated = True
            GSTZ = GameSettings.TILE_SIZE
            
            if self.check_collision(pg.Rect(nx, self.position.y, GSTZ, GSTZ)):
                if not check_teleport_and_switch(): # if so, handled in the calling function
                    self.position.x = self._snap_to_grid(self.position.x)
            else:
                self.position.x = nx

            if self.check_collision(pg.Rect(self.position.x, ny, GSTZ, GSTZ)):
                if not check_teleport_and_switch(): # if so, handled in the calling function
                    self.position.y = self._snap_to_grid(self.position.y)
            else:
                self.position.y = ny

        def bush_interaction():
            if self.game_manager.current_map.check_bush(self.hitbox) :
                self.cur = self.hitbox.centerx // GameSettings.TILE_SIZE, self.hitbox.centery // GameSettings.TILE_SIZE
                if self.updated and (self.cur != self.prev or self.prev is None):
                    self.prev = self.cur
                    self.game_manager.handle_bush_event()

                    # self.game_manager.current_map.in_bush = True

                # self.animation.set_opacity(150)
                # self.game_manager.current_map.in_bush = True    
                # print("in bush")
                pass
                # self.animation.set_opacity(255)
            else :
                # print('leved bush')
                self.prev = None
                pass
        def player_interaction():
            if self.game_manager.check_players_collision(self.hitbox) :
                # self.game_manager.handle_player_event()
                if input_manager.key_pressed(pg.K_k) : 
                    self.game_manager.handle_player_interaction(pg.K_k)
                pass
        
        update_position(dis, dt)
        bush_interaction()
        
        player_interaction()
    

        super().update(dt)

    def check_collision(self, rect: pg.Rect) -> bool:
        return self.game_manager.check_collision(rect) | self.game_manager.current_map.check_collision(rect)
    
    def lock_movement(self, duration: float = 0.5) -> None:
        self.movement_lock_timer = duration

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

