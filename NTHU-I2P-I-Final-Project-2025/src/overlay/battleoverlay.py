import pygame as pg
from src.data.bag import Bag
from src.overlay.overlay import Overlay
from src.interface.components import Button, Checkbox, Slider
from src.core.services import scene_manager, sound_manager, input_manager, get_game_manager
from src.core import GameManager
from src.utils import GameSettings
from typing import Any, override


class BattleOverlay(Overlay):
    def __init__(self, load_callback = None):
        self.close_button = None
        
        
        self.rectcolor = (0, 0 , 0)
        self.is_active = False
        self.popup_width = GameSettings.SCREEN_WIDTH
        self.popup_height = GameSettings.SCREEN_HEIGHT * 0.2
        self.popup_x = 0
        # self.popup_x = (GameSettings.SCREEN_WIDTH - self.popup_width) // 2
        self.popup_y = (GameSettings.SCREEN_HEIGHT - self.popup_height)
        self.game_manager: GameManager | None = None

        self.game_manager  = get_game_manager()
        

    @override
    def update(self, dt: float):
        
        return super().update(dt)
        
    @override
    def draw(self, screen):
        return super().draw(screen) 
    
    def update_content(self, dt: float):
        pass

    def draw_content(self, screen: pg.Surface):
        pass