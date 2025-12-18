"""
Map button component for opening the full map overlay.
"""
import pygame as pg
from typing import Callable
from .button import Button


class MapButton(Button):
    """
    地圖按鈕 - 用於開啟大地圖界面
    繼承自 Button，提供地圖專用的功能
    """
    
    def __init__(self, x: int, y: int, width: int, height: int, on_click: Callable[[int], None] | None = None):
        """
        Initialize map button.
        
        Args:
            x: X position
            y: Y position
            width: Button width
            height: Button height
            on_click: Callback function when clicked
        """
        # TODO: Create proper map button images (button_map.png, button_map_hover.png)
        # Temporarily using shop button as placeholder
        super().__init__(
            img_path="UI/button_shop.png",
            img_hovered_path="UI/button_shop_hover.png",
            x=x, y=y, width=width, height=height,
            on_click=on_click
        )
