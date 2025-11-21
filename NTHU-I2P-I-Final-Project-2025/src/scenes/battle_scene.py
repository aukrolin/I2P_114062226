import pygame as pg

from src.utils import GameSettings
from src.sprites import BackgroundSprite
from src.scenes.scene import Scene
from src.interface.components import Button
from src.overlay.settings_overlay import SettingsOverlay
from src.core.services import scene_manager, sound_manager, input_manager, set_game_manager
from typing import override

class BattleScene(Scene):
    # Background Image
    background: BackgroundSprite
    # Buttons
    play_button: Button
    
    def __init__(self) -> None:
        super().__init__()
        self.background = BackgroundSprite("backgrounds/background2.png")


        self.overlay = SettingsOverlay(lambda: set_game_manager("saves/game1.json"))

        self.overlay.close_button = self.overlay.menu_button

        

    @override
    def enter(self) -> None:
        sound_manager.play_bgm("RBY 101 Opening (Part 1).ogg")
        pass

    @override
    def exit(self) -> None:
        pass

    @override
    def update(self, dt: float) -> None:
        if input_manager.key_pressed(pg.K_SPACE):
            scene_manager.change_scene("game")
            return
        self.overlay.update(dt)

    @override
    def draw(self, screen: pg.Surface) -> None:
        self.background.draw(screen)
        self.overlay.draw(screen)   