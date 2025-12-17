import pygame as pg
from src.data.bag import Bag
from src.overlay.overlay import Overlay
from src.interface.components import Button, Checkbox, Slider
from src.core.services import scene_manager, sound_manager, input_manager, get_game_manager, resource_manager
from src.core import GameManager
from src.utils import GameSettings
from typing import Any, override


class BattleOverlay(Overlay):
    def __init__(self, battle_info=None):
        self.close_button = None
        self.battle_info = battle_info
        self.game_manager: GameManager | None = get_game_manager()
        
        # 字體設定
        self.font_large = pg.font.Font("assets/fonts/Minecraft.ttf", 28)
        self.font_medium = pg.font.Font("assets/fonts/Minecraft.ttf", 20)
        self.font_small = pg.font.Font("assets/fonts/Minecraft.ttf", 16)
        
        # 顏色定義
        self.white = (255, 255, 255)
        self.black = (0, 0, 0)
        self.hp_green = (0, 200, 0)
        self.hp_yellow = (255, 200, 0)
        self.hp_red = (200, 0, 0)
        self.hp_bg = (100, 100, 100)
        
        # UI 框架位置
        # 敵人資訊框（右上）
        self.enemy_box_width = 300
        self.enemy_box_height = 80
        self.enemy_box_x = GameSettings.SCREEN_WIDTH - self.enemy_box_width - 50
        self.enemy_box_y = 50
        
        # 玩家資訊框（左下）
        self.player_box_width = 300
        self.player_box_height = 80
        self.player_box_x = 50
        self.player_box_y = GameSettings.SCREEN_HEIGHT - 300
        
        # 寶可夢精靈圖位置
        self.enemy_sprite_x = GameSettings.SCREEN_WIDTH * 0.65
        self.enemy_sprite_y = GameSettings.SCREEN_HEIGHT * 0.25
        self.player_sprite_x = GameSettings.SCREEN_WIDTH * 0.25
        self.player_sprite_y = GameSettings.SCREEN_HEIGHT * 0.5
        
        # 快取精靈圖
        self.player_sprite = None
        self.enemy_sprite = None

    def set_battle_info(self, battle_info):
        """設定戰鬥資訊"""
        self.battle_info = battle_info
        # Force reload sprites every time
        self.player_sprite = None
        self.enemy_sprite = None
        self.load_sprites()
        print("Battle info set and sprites reloaded")
    
    def load_sprites(self):
        """載入寶可夢精靈圖"""
        if not self.battle_info or not self.game_manager:
            print("[BattleOverlay] Cannot load sprites: missing battle_info or game_manager")
            return
        
        # 載入玩家寶可夢圖片
        player_monsters = self.game_manager.bag.get_monsters()
        if player_monsters and len(player_monsters) > 0:
            player_monster = player_monsters[0]
            try:
                self.player_sprite = resource_manager.get_image(player_monster['sprite_path'])
                # 放大圖片（可調整倍數）
                self.player_sprite = pg.transform.scale(self.player_sprite, 
                    (int(self.player_sprite.get_width() * 3), 
                     int(self.player_sprite.get_height() * 3)))
                print(f"[BattleOverlay] Loaded player sprite: {player_monster['name']}")
            except Exception as e:
                print(f"[BattleOverlay] Failed to load player sprite: {e}")
                self.player_sprite = None
        
        # 載入敵人寶可夢圖片
        if 'bush_pokemon' in self.battle_info:
            enemy_monster = self.battle_info['bush_pokemon']
            print(f"[BattleOverlay] Loading bush pokemon: {enemy_monster.get('name', 'Unknown')}")
        elif 'bag' in self.battle_info:
            enemy_monsters = self.battle_info['bag'].get_monsters()
            enemy_monster = enemy_monsters[0] if enemy_monsters else None
            print(f"[BattleOverlay] Loading enemy from bag: {enemy_monster.get('name', 'Unknown') if enemy_monster else 'None'}")
        else:
            enemy_monster = None
            print(f"[BattleOverlay] No enemy monster found in battle_info")
        
        if enemy_monster:
            try:
                self.enemy_sprite = resource_manager.get_image(enemy_monster['sprite_path'])
                # 放大圖片
                self.enemy_sprite = pg.transform.scale(self.enemy_sprite,
                    (int(self.enemy_sprite.get_width() * 3),
                     int(self.enemy_sprite.get_height() * 3)))
                print(f"[BattleOverlay] Loaded enemy sprite: {enemy_monster['name']}")
            except Exception as e:
                print(f"[BattleOverlay] Failed to load enemy sprite: {e}")
                self.enemy_sprite = None

    def draw_hp_bar(self, screen, x, y, width, height, current_hp, max_hp):
        """繪製 HP 條"""
        # 背景
        pg.draw.rect(screen, self.hp_bg, (x, y, width, height))
        
        # HP 比例
        hp_ratio = max(0, current_hp / max_hp) if max_hp > 0 else 0
        hp_width = int(width * hp_ratio)
        
        # HP 顏色（綠 > 黃 > 紅）
        if hp_ratio > 0.5:
            hp_color = self.hp_green
        elif hp_ratio > 0.2:
            hp_color = self.hp_yellow
        else:
            hp_color = self.hp_red
        
        # 繪製 HP
        if hp_width > 0:
            pg.draw.rect(screen, hp_color, (x, y, hp_width, height))
        
        # 邊框
        pg.draw.rect(screen, self.black, (x, y, width, height), 2)

    def draw_pokemon_info(self, screen, x, y, width, height, pokemon_data, is_enemy=False):
        """繪製寶可夢資訊框"""
        # 背景框
        bg_color = (240, 240, 240)
        pg.draw.rect(screen, bg_color, (x, y, width, height))
        pg.draw.rect(screen, self.black, (x, y, width, height), 3)
        
        # 名稱和等級
        name_text = self.font_medium.render(f"{pokemon_data['name']}", True, self.black)
        level_text = self.font_small.render(f"Lv.{pokemon_data['level']}", True, self.black)
        screen.blit(name_text, (x + 10, y + 10))
        screen.blit(level_text, (x + width - 60, y + 10))
        
        # HP 條
        hp_bar_x = x + 10
        hp_bar_y = y + 45
        hp_bar_width = width - 20
        hp_bar_height = 12
        self.draw_hp_bar(screen, hp_bar_x, hp_bar_y, hp_bar_width, hp_bar_height,
                        pokemon_data['hp'], pokemon_data['max_hp'])
        
        # HP 數值（只有玩家顯示具體數值）
        if not is_enemy:
            hp_text = self.font_small.render(
                f"{pokemon_data['hp']}/{pokemon_data['max_hp']}", 
                True, self.black
            )
            screen.blit(hp_text, (x + 10, y + 62))

    @override
    def update(self, dt: float):
        self.update_content(dt)
        
    @override
    def draw(self, screen):
        self.draw_content(screen)
    
    def update_content(self, dt: float):
        pass

    def draw_content(self, screen: pg.Surface):
        """繪製戰鬥 UI"""
        if not self.battle_info or not self.game_manager:
            return
        
        # 獲取玩家寶可夢
        player_monsters = self.game_manager.bag.get_monsters()
        if not player_monsters or len(player_monsters) == 0:
            return
        player_monster = player_monsters[0]
        
        # 獲取敵人寶可夢
        if 'bush_pokemon' in self.battle_info:
            enemy_monster = self.battle_info['bush_pokemon']
        elif 'bag' in self.battle_info:
            enemy_monsters = self.battle_info['bag'].get_monsters()
            if not enemy_monsters or len(enemy_monsters) == 0:
                print("[BattleOverlay] Warning: No enemy monsters in bag")
                return
            enemy_monster = enemy_monsters[0]
        else:
            print("[BattleOverlay] Warning: No valid enemy data in battle_info")
            return
        
        if not enemy_monster:
            print("[BattleOverlay] Warning: enemy_monster is None")
            return
        
        # 繪製敵人精靈圖
        if self.enemy_sprite:
            sprite_rect = self.enemy_sprite.get_rect(center=(self.enemy_sprite_x, self.enemy_sprite_y))
            screen.blit(self.enemy_sprite, sprite_rect)
        
        # 繪製玩家精靈圖
        if self.player_sprite:
            sprite_rect = self.player_sprite.get_rect(center=(self.player_sprite_x, self.player_sprite_y))
            screen.blit(self.player_sprite, sprite_rect)
        
        # 繪製敵人資訊框
        self.draw_pokemon_info(screen, self.enemy_box_x, self.enemy_box_y,
                              self.enemy_box_width, self.enemy_box_height,
                              enemy_monster, is_enemy=True)
        
        # 繪製玩家資訊框
        self.draw_pokemon_info(screen, self.player_box_x, self.player_box_y,
                              self.player_box_width, self.player_box_height,
                              player_monster, is_enemy=False)