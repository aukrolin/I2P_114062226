
import pygame as pg
from .component import UIComponent
from typing import Callable, override
from src.core.services import input_manager
from src.utils import Logger

class Checkbox(UIComponent):
    def __init__(self, x: int, y: int, size: int, checked: bool = False, callback=None):
        self.rect = pg.Rect(x, y, size, size)
        self.checked = checked
        self.callback = callback
        self.hovered = False
        self.font = pg.font.Font(None, 24)  # 創建字體

    @override
    def update(self, dt: float):
        if self.rect.collidepoint(input_manager.mouse_pos):
            # Logger.debug(f"[~] Button hover")
            self.hovered = True 
            if input_manager.mouse_pressed(1):
                self.checked = not self.checked
                Logger.info(f"[+] Button clicked")
                if self.callback:
                    self.callback(self.checked)




    @override    
    def draw(self, screen: pg.Surface):
        """繪製 checkbox"""
        # 繪製外框
        color = (100, 100, 100) if not self.hovered else (150, 150, 150)
        pg.draw.rect(screen, color, self.rect, 2)
        
        # 如果選中，繪製勾選標記
        if self.checked:
            pg.draw.line(screen, (0, 200, 0), 
                        (self.rect.left + 5, self.rect.top + 5),
                        (self.rect.right - 5, self.rect.bottom - 5), 3)
            pg.draw.line(screen, (0, 200, 0),
                        (self.rect.right - 5, self.rect.top + 5),
                        (self.rect.left + 5, self.rect.bottom - 5), 3)
        text_surface = self.font.render('on' if self.checked else 'off', True, (0, 0, 0))
        text_x = self.rect.right + 10  # 滑塊右邊 10 像素
        text_y = self.rect.centery - text_surface.get_height() // 2  # 垂直置中
        screen.blit(text_surface, (text_x, text_y))