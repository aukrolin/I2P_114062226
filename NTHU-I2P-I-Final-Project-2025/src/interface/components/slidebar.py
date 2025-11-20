"""
Slider UI 組件
"""
import pygame as pg
from .component import UIComponent
from typing import Callable, override
from src.core.services import input_manager
from src.utils import Logger



class Slider:
    """滑塊組件"""
    def __init__(self, x: int, y: int, width: int, height: int, 
                 min_val: float = 0.0, max_val: float = 1.0, 
                 initial_val: float = 0.5, callback=None):
        self.rect = pg.Rect(x, y, width, height)
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        self.callback = callback
        self.dragging = False
        self.knob_radius = height // 2 + 2
        self._knob_x = 0
        self.font = pg.font.Font(None, 24)  # 創建字體

    def _get_knob_x(self) -> int:
        """計算滑塊把手的 x 座標"""
        ratio = (self.value - self.min_val) / (self.max_val - self.min_val)
        return int(self.rect.left + ratio * self.rect.width)
    def _update_value(self, mouse_x: int):
        """更新滑塊值"""
        # 限制在滑塊範圍內
        x = max(self.rect.left, min(mouse_x, self.rect.right))
        ratio = (x - self.rect.left) / self.rect.width
        self.value = self.min_val + ratio * (self.max_val - self.min_val)
        
        if self.callback:
            self.callback(self.value)

    @override
    def update(self, dt: float) -> None:
        self._knob_x = self._get_knob_x()
        self.knob_rect = pg.Rect(self._knob_x - self.knob_radius, 
                        self.rect.centery - self.knob_radius,
                        self.knob_radius * 2, self.knob_radius * 2)
        
        # 檢查是否剛按下鼠標（開始拖動）
        if input_manager.mouse_pressed(1):
            # 點擊 knob 或滑塊軌道都可以開始拖動
            if self.knob_rect.collidepoint(input_manager.mouse_pos) or self.rect.collidepoint(input_manager.mouse_pos):
                self.dragging = True
        if input_manager.mouse_released(1):
            self.dragging = False
        
        # 如果正在拖動，持續更新值
        if self.dragging:

            self._update_value(input_manager.mouse_pos[0])    



    @override
    def draw(self, screen: pg.Surface):
        """繪製滑塊"""
        # 繪製軌道
        pg.draw.rect(screen, (100, 100, 100), self.rect, border_radius=self.rect.height // 2)
        
        # 繪製已填充部分
        filled_width = int((self.value - self.min_val) / (self.max_val - self.min_val) * self.rect.width)
        filled_rect = pg.Rect(self.rect.left, self.rect.top, filled_width, self.rect.height)
        pg.draw.rect(screen, (0, 150, 255), filled_rect, border_radius=self.rect.height // 2)
        
        # 繪製把手
        knob_x = self._get_knob_x()
        knob_color = (255, 255, 255) if not self.dragging else (200, 200, 200)
        pg.draw.circle(screen, knob_color, (knob_x, self.rect.centery), self.knob_radius)
        pg.draw.circle(screen, (0, 0, 0), (knob_x, self.rect.centery), self.knob_radius, 2)
        value_text = f"{self.value:.1f}"
        text_surface = self.font.render(value_text, True, (0, 0, 0))
        text_x = self.rect.right + 10  # 滑塊右邊 10 像素
        text_y = self.rect.centery - text_surface.get_height() // 2  # 垂直置中
        screen.blit(text_surface, (text_x, text_y))