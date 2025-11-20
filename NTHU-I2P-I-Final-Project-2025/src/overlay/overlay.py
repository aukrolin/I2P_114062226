import pygame as pg
from abc import ABC, abstractmethod
from src.interface.components import Button
from src.utils import GameSettings

class Overlay(ABC):
    """Overlay 基類"""
    def __init__(self):
        self.is_active = False
        self.close_button = None
        self.popup_width = GameSettings.SCREEN_WIDTH * 0.6
        self.popup_height = GameSettings.SCREEN_HEIGHT * 0.6
        self.popup_x = (GameSettings.SCREEN_WIDTH - self.popup_width) // 2
        self.popup_y = (GameSettings.SCREEN_HEIGHT - self.popup_height) // 2
        
    def set_close_callback(self, callback):
        """設置關閉按鈕的 callback"""

        TS = GameSettings.TILE_SIZE
        popup_width = GameSettings.SCREEN_WIDTH * 0.6
        popup_height = GameSettings.SCREEN_HEIGHT * 0.6
        popup_x = (GameSettings.SCREEN_WIDTH - popup_width) // 2
        popup_y = (GameSettings.SCREEN_HEIGHT - popup_height) // 2
        self.close_button = Button(
            "UI/button_back.png", 
            "UI/button_back_hover.png",
            popup_x + TS, popup_y+popup_height-TS, TS, TS,
            callback
        )
    
    @abstractmethod
    def draw_content(self, screen: pg.Surface):
        """子類實現具體內容的繪製"""
        pass
    @abstractmethod
    def update_content(self, dt: float):
        """子類實現具體內容的更新"""
        pass
    def update(self, dt: float):
        """更新 Overlay 狀態"""
        self.close_button.update(dt)
        self.update_content(dt)
        pass

    def draw(self, screen: pg.Surface):
        """繪製 overlay 框架"""
        # 繪製背景框

        popup_rect = pg.Rect(self.popup_x, self.popup_y, self.popup_width, self.popup_height)
        pg.draw.rect(screen, (255, 200, 100), popup_rect)
        pg.draw.rect(screen, (0, 0, 0), popup_rect, 3)
        
        # 繪製具體內容
        self.draw_content(screen)
        
        # 繪製關閉按鈕
        if self.close_button:
            self.close_button.draw(screen)
    
    def handle_events(self, events):
        """處理事件"""
        if self.close_button:
            for event in events:
                self.close_button.handle_event(event)