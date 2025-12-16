import pygame as pg
import signal
import sys

from src.utils import GameSettings, Logger
from .services import scene_manager, input_manager, set_game_manager
from src.scenes.menu_scene import MenuScene
from src.scenes.game_scene import GameScene
from src.scenes.setting_scene import SettingsScene
from src.scenes.battle_scene import BattleScene

class Engine:

    screen: pg.Surface              # Screen Display of the Game
    clock: pg.time.Clock            # Clock for FPS control
    running: bool                   # Running state of the game

    def __init__(self):
        Logger.info("Initializing Engine")

        pg.init()

        self.screen = pg.display.set_mode((GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT))
        self.clock = pg.time.Clock()
        self.running = True

        pg.display.set_caption(GameSettings.TITLE)
        set_game_manager("saves/start.json")

        # Setup signal handler for Ctrl-C
        signal.signal(signal.SIGINT, self._signal_handler)

        scene_manager.register_scene("menu", MenuScene())
        scene_manager.register_scene("game", GameScene())
        scene_manager.register_scene("settings", SettingsScene())
        scene_manager.register_scene("battle", BattleScene())
        '''
        [TODO HACKATHON 5]
        Register the setting scene here
        '''
        scene_manager.change_scene("menu")
    
    def _signal_handler(self, sig, frame):
        """Handle Ctrl-C (SIGINT) for graceful shutdown"""
        Logger.info("Received interrupt signal (Ctrl-C), shutting down...")
        self.running = False

    def run(self):
        Logger.info("Running the Game Loop ...")

        try:
            while self.running:
                dt = self.clock.tick(GameSettings.FPS) / 1000.0
                self.handle_events()
                self.update(dt)
                self.render()
        finally:
            # Always cleanup regardless of how we exit
            self.cleanup()

    def handle_events(self):
        input_manager.reset()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                Logger.info("Window close requested, shutting down...")
                self.running = False
            input_manager.handle_events(event)

    def update(self, dt: float):
        scene_manager.update(dt)

    def render(self):
        self.screen.fill((0, 0, 0))     # Make sure the display is cleared
        scene_manager.draw(self.screen) # Draw the current scene
        pg.display.flip()               # Render the display

    def cleanup(self):
        """Cleanup resources before shutdown"""
        Logger.info("Cleaning up resources...")
        
        # Stop online manager if active
        try:
            from src.core.services import get_ids
            for id in get_ids():
                Logger.info(f"Appending id {id} on exit")
                # TODO : Send a proper disconnect message to server if needed
        except Exception as e:
            Logger.warning(f"Error stopping online manager: {e}")
        
            

        # Quit pygame
        pg.quit()
        Logger.info("Shutdown complete")

    