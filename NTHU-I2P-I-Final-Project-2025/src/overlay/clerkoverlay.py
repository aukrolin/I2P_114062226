import pygame as pg
from src.data.bag import Bag
from src.overlay.overlay import Overlay
from src.interface.components import Button, Checkbox, Slider
from src.core.services import scene_manager, sound_manager, input_manager, get_game_manager
from src.core import GameManager
from src.utils import GameSettings
from typing import Any, override

class ClerkOverlay(Overlay):
    """背包彈窗"""
    def __init__(self, ):
        super().__init__()
        self.clerk: Bag | None = None

    
    def draw_content(self, screen: pg.Surface):
        """繪製背包內容"""
        self.player_item = get_game_manager().bag.get_items()
        self.clerk_item = self.clerk.get_selling_items()
        y_offset = GameSettings.SCREEN_HEIGHT*0.4
        # print(self.clerk_item)
        x = 300
        for selling in self.clerk_item:
            font = pg.font.Font(None, 24)
            text = font.render(f"{selling['name']} - Price: {selling['price']}", True, (0, 0, 0))
            screen.blit(text, (x+50, y_offset))

            screen.blit(self.get_sprite(selling['sprite_path']), (x, y_offset))
            y_offset += 40
            for shop_button in self.shops:
                shop_button.draw(screen)

    def get_sprite(self, path: str) -> pg.Surface | None:
        """根據路徑獲取精靈圖像"""
        try:
            return pg.image.load(f'assets/images/{path}').convert_alpha()
        except Exception as e:
            print(f"Failed to load sprite from {path}: {e}")
            return None

    def update_overlay(self, info):
        self.clerk = info.get("bag", None)
        self.clerk_item = self.clerk.get_selling_items()
        self.shops = []
        x = 300
        y_offset = GameSettings.SCREEN_HEIGHT*0.4  - 10

        for i in range(len(self.clerk_item)):
            self.shops.append(Button(
                "UI/button_shop.png", "UI/button_shop_hover.png",
                x + 300, y_offset, GameSettings.TILE_SIZE*0.5, 40,
                lambda id: self.shop_item(self.clerk_item[id]), idx=i
                )
            )
            y_offset += 40
        # for 
        # return super().update_overlay(info) 
    def shop_item(self, item: Any):
        # pass
        # print(item)
        # print
        player_bag: Bag = get_game_manager().bag
        player_item = player_bag.get_items()
        item_price = item["price"]
        money = [i for i in player_item if i["name"] == "Coins"][0]


        if money["count"] >= item_price:
            player_bag.substract_item({"name": "Coins"}, item_price)
            player_bag.add_item(item)
            print(f"Purchased {item['name']} for {item_price}")
        else:
            print(f"Not enough money to purchase {item['name']}. Needed: {item_price}, Available: {money['count']}")
    def update_gm(self, game_manager):
        super().update_gm(game_manager)
    def update_content(self, dt: float):
        for shop_button in self.shops:
            shop_button.update(dt)

        pass