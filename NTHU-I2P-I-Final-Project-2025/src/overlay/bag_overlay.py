"""
背包 Overlay
"""
import pygame as pg
from src.data.bag import Bag
from src.overlay.overlay import Overlay


class BagOverlay(Overlay):
    """背包彈窗"""
    def __init__(self, bag: Bag):
        super().__init__()
        self.bag : Bag = bag  # 只持有數據的引用
    
    def draw_content(self, screen: pg.Surface):
        """繪製背包內容"""
        # 繪製怪獸列表
        y_offset = 100
        for monster in self.bag._monsters_data:
            # 繪製怪獸信息
            font = pg.font.Font(None, 24)
            text = font.render(f"{monster['name']} - HP: {monster['hp']}/{monster['max_hp'] }", True, (0, 0, 0))
            screen.blit(text, (150, y_offset))
            y_offset += 40
    def update_content(self, dt: float):
        pass