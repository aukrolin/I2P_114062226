"""
背包 Overlay
"""
import pygame as pg
from src.data.bag import Bag
from src.overlay.overlay import Overlay
from src.interface.components import Button, Checkbox, Slider
from src.core.services import scene_manager, sound_manager, input_manager, get_game_manager
from src.core import GameManager
from src.utils import GameSettings
class SettingsOverlay(Overlay):
    """設置彈窗"""
    def __init__(self, load_callback = None):
        super().__init__()
        self.mutebox = Checkbox(self.popup_width//2, self.popup_y + 100, 30, False, lambda checked: sound_manager.mute() if checked else sound_manager.unmute())
        self.volumeslider = Slider(
            self.popup_x + 100, self.popup_y + 200, 
            self.popup_width - 200, 20,
            0, 100, 50, 
            lambda val: sound_manager.set_volume(val/100)
        )
        px, py = GameSettings.SCREEN_WIDTH // 2, GameSettings.SCREEN_HEIGHT * 3 // 4

        self.menu_button = Button(
            "UI/button_back.png", "UI/button_back_hover.png",
            self.popup_x + 2 * GameSettings.TILE_SIZE, py, 1.5*GameSettings.TILE_SIZE, 1.5*GameSettings.TILE_SIZE,
            lambda: scene_manager.change_scene("menu")
        )

        
        game_manager  = get_game_manager()
        if game_manager : 

            self.save_button = Button (
                "UI/button_save.png", "UI/button_save_hover.png",
                self.popup_x + self.popup_width//4 - 75, self.popup_y + self.popup_height - 150,
                150, 50,
                lambda: game_manager.save(path="saves/game1.json")
            )

            self.load_button = Button (
                "UI/button_load.png", "UI/button_load_hover.png",
                self.popup_x + self.popup_width*3//4 - 75, self.popup_y + self.popup_height - 150,
                150, 50,
                load_callback if load_callback else lambda: None
            )
            # print()
        
    
    
    def update_content(self, dt: float):
        self.mutebox.update(dt)
        self.volumeslider.update(dt)
        self.menu_button.update(dt)
        if hasattr(self, 'save_button'):
            self.save_button.update(dt)
        if hasattr(self, 'load_button'):
            self.load_button.update(dt)
        # print(sound_manager.volume)

    def draw_content(self, screen: pg.Surface):
        self.mutebox.draw(screen)
        self.volumeslider.draw(screen)
        self.menu_button.draw(screen)
        if hasattr(self, 'save_button'):
            self.save_button.draw(screen)
        if hasattr(self, 'load_button'):
            self.load_button.draw(screen)