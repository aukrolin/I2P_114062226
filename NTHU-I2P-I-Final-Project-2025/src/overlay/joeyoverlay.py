"""
背包 Overlay
"""
import pygame as pg
from src.data.bag import Bag
from src.overlay.overlay import Overlay
from src.core import GameManager
from src.core.services import get_game_manager

class JoeyOverlay(Overlay):
    """背包彈窗"""
    def __init__(self, ):
        super().__init__()
    
    def draw_content(self, screen: pg.Surface):
        """繪製背包內容"""
        # 繪製怪獸列表
        self.bag= get_game_manager().bag
        y_offset = 100
        for monster in self.bag.get_monsters():
            # 繪製怪獸信息
            font = pg.font.Font(None, 24)
            text = font.render(f"{monster['name']} - HP: {monster['hp']}/{monster['max_hp'] }", True, (0, 0, 0))
            screen.blit(text, (150, y_offset))
            # Render monster sprite if available

            screen.blit(self.get_sprite(monster['sprite_path']), (100, y_offset))
            
            y_offset += 40
        for item in self.bag.get_items():
            font = pg.font.Font(None, 24)
            text = font.render(f"{item['name']} x{item['count']}", True, (0, 0, 0))
            screen.blit(text, (400, y_offset))

            screen.blit(self.get_sprite(item['sprite_path']), (350, y_offset))
            y_offset += 40

    def get_sprite(self, path: str) -> pg.Surface | None:
        """根據路徑獲取精靈圖像"""
        try:
            return pg.image.load(f'assets/images/{path}').convert_alpha()
        except Exception as e:
            print(f"Failed to load sprite from {path}: {e}")
            return None


    def update_gm(self, game_manager):
        super().update_gm(game_manager)
    def update_content(self, dt: float):
        pass