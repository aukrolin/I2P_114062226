"""
背包 Overlay
"""
import pygame as pg
from src.data.bag import Bag
from src.overlay.overlay import Overlay
from src.core import GameManager
from src.core.services import get_game_manager, input_manager
from src.utils.evolution_manager import can_evolve_with_item, evolve_monster

class BagOverlay(Overlay):
    """背包彈窗"""
    def __init__(self, ):
        super().__init__()
        self.selected_item_index = 0
        self.selected_pokemon_index = 0
        self.mode = "items"  # "items" 或 "pokemon_select"
        self.selected_item_for_evolution = None
        self.message = ""
        self.message_timer = 0.0
    
    def draw_content(self, screen: pg.Surface):
        """繪製背包內容"""
        self.bag = get_game_manager().bag
        font = pg.font.Font(None, 24)
        title_font = pg.font.Font(None, 32)
        
        if self.mode == "items":
            # 顯示物品列表
            title = title_font.render("Bag - Items (Use W/S to select, Space to use)", True, (0, 0, 0))
            screen.blit(title, (50, 50))
            
            y_offset = 100
            items = self.bag.get_items()
            
            for i, item in enumerate(items):
                if item['count'] <= 0:
                    continue
                    
                prefix = "->" if i == self.selected_item_index else "  "
                color = (255, 100, 100) if i == self.selected_item_index else (0, 0, 0)
                
                text = font.render(f"{prefix}{item['name']} x{item['count']}", True, color)
                screen.blit(text, (400, y_offset))
                
                sprite = self.get_sprite(item['sprite_path'])
                if sprite:
                    screen.blit(sprite, (350, y_offset))
                
                y_offset += 40
            
            # 顯示寶可夢列表（左側）
            y_offset = 100
            for monster in self.bag.get_monsters():
                text = font.render(f"{monster['name']} - HP: {monster['hp']}/{monster['max_hp']}", True, (0, 0, 0))
                screen.blit(text, (150, y_offset))
                
                sprite = self.get_sprite(monster['sprite_path'])
                if sprite:
                    screen.blit(sprite, (100, y_offset))
                
                y_offset += 40
        
        elif self.mode == "pokemon_select":
            # 選擇寶可夢模式
            title = title_font.render(f"Use {self.selected_item_for_evolution['name']} on which Pokemon?", True, (0, 0, 0))
            screen.blit(title, (50, 50))
            
            instructions = font.render("W/S to select, Space to confirm, ESC to cancel", True, (100, 100, 100))
            screen.blit(instructions, (50, 80))
            
            y_offset = 120
            monsters = self.bag.get_monsters()
            
            for i, monster in enumerate(monsters):
                prefix = "->" if i == self.selected_pokemon_index else "  "
                color = (255, 100, 100) if i == self.selected_pokemon_index else (0, 0, 0)
                
                # 檢查是否可以進化
                can_evolve = can_evolve_with_item(monster, self.selected_item_for_evolution)
                evolution_text = " (Can evolve!)" if can_evolve else ""
                
                text = font.render(
                    f"{prefix}{monster['name']} Lv.{monster['level']} - HP: {monster['hp']}/{monster['max_hp']}{evolution_text}",
                    True, color
                )
                screen.blit(text, (150, y_offset))
                
                sprite = self.get_sprite(monster['sprite_path'])
                if sprite:
                    screen.blit(sprite, (100, y_offset))
                
                y_offset += 40
        
        # 顯示訊息
        if self.message:
            message_surface = font.render(self.message, True, (0, 200, 0))
            screen.blit(message_surface, (50, 500))

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
        """更新內容，處理輸入"""
        # 訊息計時器
        if self.message_timer > 0:
            self.message_timer -= dt
            if self.message_timer <= 0:
                self.message = ""
        
        bag = get_game_manager().bag
        
        if self.mode == "items":
            # 物品選擇模式
            items = [item for item in bag.get_items() if item['count'] > 0]
            
            if not items:
                return
            
            # 上下選擇
            if input_manager.key_pressed(pg.K_w) or input_manager.key_pressed(pg.K_UP):
                self.selected_item_index = (self.selected_item_index - 1) % len(items)
            elif input_manager.key_pressed(pg.K_s) or input_manager.key_pressed(pg.K_DOWN):
                self.selected_item_index = (self.selected_item_index + 1) % len(items)
            
            # 使用物品
            elif input_manager.key_pressed(pg.K_SPACE) or input_manager.key_pressed(pg.K_k):
                selected_item = items[self.selected_item_index]
                
                # 檢查是否是進化石
                if selected_item.get("effect") == "evolution":
                    # 進入寶可夢選擇模式
                    self.mode = "pokemon_select"
                    self.selected_item_for_evolution = selected_item
                    self.selected_pokemon_index = 0
                    print(f"[BagOverlay] Entering pokemon selection for {selected_item['name']}")
                else:
                    # 其他物品（目前不處理）
                    self.message = f"{selected_item['name']} can only be used in battle!"
                    self.message_timer = 2.0
        
        elif self.mode == "pokemon_select":
            # 寶可夢選擇模式
            monsters = bag.get_monsters()
            
            # 上下選擇
            if input_manager.key_pressed(pg.K_w) or input_manager.key_pressed(pg.K_UP):
                self.selected_pokemon_index = (self.selected_pokemon_index - 1) % len(monsters)
            elif input_manager.key_pressed(pg.K_s) or input_manager.key_pressed(pg.K_DOWN):
                self.selected_pokemon_index = (self.selected_pokemon_index + 1) % len(monsters)
            
            # 確認進化
            elif input_manager.key_pressed(pg.K_SPACE) or input_manager.key_pressed(pg.K_k):
                selected_monster = monsters[self.selected_pokemon_index]
                
                # 檢查是否可以進化
                if can_evolve_with_item(selected_monster, self.selected_item_for_evolution):
                    # 執行進化
                    evolved_monster, messages = evolve_monster(selected_monster)
                    
                    # 更新寶可夢數據
                    monsters[self.selected_pokemon_index] = evolved_monster
                    
                    # 消耗道具
                    self.selected_item_for_evolution['count'] -= 1
                    
                    # 顯示訊息
                    self.message = " ".join(messages)
                    self.message_timer = 5.0
                    
                    print(f"[BagOverlay] Evolution complete: {messages}")
                    
                    # 返回物品模式
                    self.mode = "items"
                    self.selected_item_for_evolution = None
                else:
                    self.message = f"{selected_monster['name']} cannot evolve with this item!"
                    self.message_timer = 2.0
            
            # 取消
            elif input_manager.key_pressed(pg.K_ESCAPE):
                self.mode = "items"
                self.selected_item_for_evolution = None
                print("[BagOverlay] Cancelled pokemon selection")