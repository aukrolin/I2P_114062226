import pygame as pg
import threading
import time

from src.scenes.scene import Scene
from src.core import GameManager, OnlineManager
from src.core.services import scene_manager, get_game_manager, set_game_manager
from src.interface.components import Button
from src.utils import Logger, PositionCamera, GameSettings, Position
from src.core.services import sound_manager
from src.sprites import Sprite
from src.overlay import BagOverlay, SettingsOverlay, Overlay
# from src
from typing import override

class GameScene(Scene):
    online_manager: OnlineManager | None
    sprite_online: Sprite


    def __init__(self):
        super().__init__()
        self.show_overlay = False  # 控制是否显示 overlay

        
        self.overlays : dict[str, Overlay] = {
            'bag': BagOverlay(),
            'settings': SettingsOverlay(lambda: set_game_manager("saves/game1.json"))
        }       
        self.game_manager: GameManager = get_game_manager()
        # Online Manager
        if GameSettings.IS_ONLINE:
            self.online_manager = OnlineManager()
        else:
            self.online_manager = None
        self.sprite_online = Sprite("ingame_ui/options1.png", (GameSettings.TILE_SIZE, GameSettings.TILE_SIZE))



        for overlay in self.overlays.values():
            overlay.set_close_callback(self.overlay_close)
        self.current_overlay = None

        TS = GameSettings.TILE_SIZE
        px = GameSettings.SCREEN_WIDTH - TS *2
        py = TS 
        self.bag_button = Button(
            "UI/button_backpack.png", "UI/button_backpack_hover.png",
            px+TS/2, py, TS, TS,
            lambda: self.bag_overlay()
        )
        self.settings_button = Button(
            "UI/button_setting.png", "UI/button_setting_hover.png",
            px-TS, py, TS, TS,
            lambda: self.settings_overlay()
        )
    
        


    def bag_overlay(self):
        self.overlay_open()
        self.overlay = 'bag'
        Logger.info('Open bag overlay')
    def settings_overlay(self):
        self.overlay_open()
        self.overlay = 'settings'
        Logger.info('Open settings overlay')


    def overlay_open(self):
        self.show_overlay = True
        self.game_manager.pause_game()
    def overlay_close(self):
        self.show_overlay = False
        self.overlay = None
        self.game_manager.resume_game()

    


    
    @override
    def enter(self) -> None:
        sound_manager.play_bgm("RBY 103 Pallet Town.ogg")
        if self.online_manager:
            self.online_manager.enter()
        
    @override
    def exit(self) -> None:
        if self.online_manager:
            self.online_manager.exit()
        
    @override
    def update(self, dt: float):
        # Check if there is assigned next scene
        self.game_manager = get_game_manager()
        self.game_manager.try_switch_map()
        
        # Update player and other data
        if self.game_manager.player:
            self.game_manager.player.update(dt)
        for enemy in self.game_manager.current_enemy_trainers:
            enemy.update(dt)
            
        # Update others
        self.bag_button.update(dt)
        self.settings_button.update(dt)

        if self.show_overlay and self.overlay:
            self.overlays[self.overlay].update(dt)
        
         # Update online manager


        if self.game_manager.player is not None and self.online_manager is not None:
            _ = self.online_manager.update(
                self.game_manager.player.position.x, 
                self.game_manager.player.position.y,
                self.game_manager.current_map.path_name
            )
        
    @override
    def draw(self, screen: pg.Surface):        
        if self.game_manager.player:
            '''
            [TODO HACKATHON 3]
            Implement the camera algorithm logic here
            Right now it's hard coded, you need to follow the player's positions
            you may use the below example, but the function still incorrect, you may trace the entity.py
            
            camera = self.game_manager.player.camera
            '''
            P = self.game_manager.player
            camera = P.camera
            self.game_manager.current_map.draw(screen, camera)
            self.game_manager.player.draw(screen, camera)
        else:
            camera = PositionCamera(0, 0)
            self.game_manager.current_map.draw(screen, camera)
        for enemy in self.game_manager.current_enemy_trainers:
            enemy.draw(screen, camera)
        if self.show_overlay:
            # 创建半透明黑色遮罩
            overlay_surface = pg.Surface((GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT))
            overlay_surface.set_alpha(128)  # 0-255，128 是半透明
            overlay_surface.fill((0, 0, 0))  # 黑色
            screen.blit(overlay_surface, (0, 0))
            self.overlays[self.overlay].draw(screen)



        self.bag_button.draw(screen)

        self.settings_button.draw(screen)
        
         # Draw online players



        if self.online_manager and self.game_manager.player:
            list_online = self.online_manager.get_list_players()
            for player in list_online:
                if player["map"] == self.game_manager.current_map.path_name:
                    cam = self.game_manager.player.camera
                    pos = cam.transform_position_as_position(Position(player["x"], player["y"]))
                    self.sprite_online.update_pos(pos)
                    self.sprite_online.draw(screen)
