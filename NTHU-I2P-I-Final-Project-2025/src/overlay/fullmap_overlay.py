"""
Full Map Overlay - 大地圖界面
顯示完整地圖縮小版，並提供地標導航功能
"""
import pygame as pg
from typing import Callable, List, Tuple
from src.overlay.overlay import Overlay
from src.interface.components import Button
from src.utils import GameSettings, Position, Teleport
from src.utils.pathfinding import PathfindingGrid, a_star, pixel_to_tile, tile_to_pixel
from src.core.services import get_game_manager, get_navigation_manager
from src.utils import Logger


class FullMapOverlay(Overlay):
    """
    大地圖 Overlay
    - 顯示完整地圖縮小版
    - 顯示地標列表（從 teleporters 獲取）
    - 提供導航按鈕
    """
    
    def __init__(self):
        super().__init__()
        
        # Map display settings
        self.map_display_width = self.popup_width * 0.6  # 左側 60% 用於顯示地圖
        self.map_display_height = self.popup_height * 0.9  # 90% 高度用於地圖
        self.map_display_x = self.popup_x + 20
        self.map_display_y = self.popup_y + 40
        
        # Landmark list settings
        self.landmark_list_x = self.popup_x + self.map_display_width + 40
        self.landmark_list_y = self.popup_y + 60
        self.landmark_list_width = self.popup_width * 0.35
        
        # Navigation buttons
        self.navigate_buttons: List[Button] = []
        self.landmarks: List[Tuple[str, Position]] = []  # (name, position)
        
        # Map surface (will be generated when overlay opens)
        self.map_surface: pg.Surface | None = None
        self.map_scale: float = 1.0
        
    def open(self):
        """當 overlay 開啟時調用，生成地圖和地標列表"""
        self.is_active = True
        self._generate_map_and_landmarks()
        
    def _generate_map_and_landmarks(self):
        """生成地圖縮略圖和地標列表"""
        game_manager = get_game_manager()
        current_map = game_manager.current_map
        
        if not current_map:
            Logger.warning("No current map found!")
            return
            
        # Get map dimensions
        map_width_pixels = current_map.tmxdata.width * GameSettings.TILE_SIZE
        map_height_pixels = current_map.tmxdata.height * GameSettings.TILE_SIZE
        
        # Calculate scale to fit in display area
        scale_x = self.map_display_width / map_width_pixels
        scale_y = self.map_display_height / map_height_pixels
        self.map_scale = min(scale_x, scale_y)
        
        # Create scaled map surface
        scaled_width = int(map_width_pixels * self.map_scale)
        scaled_height = int(map_height_pixels * self.map_scale)
        self.map_surface = pg.transform.scale(current_map._surface, (scaled_width, scaled_height))
        
        # Generate landmarks from teleporters
        self.landmarks = []
        self.navigate_buttons = []
        print(current_map.teleporters)
        for i, tp in enumerate(current_map.teleporters):
            # Extract landmark name from destination
            landmark_name = self._format_landmark_name(tp.destination)
            self.landmarks.append((landmark_name, tp.pos))
            
            # Create navigate button
            button_y = self.landmark_list_y + i * 70
            button = Button(
                img_path="UI/button_backpack.png",  # Placeholder, will need proper navigate button
                img_hovered_path="UI/button_backpack_hover.png",
                x=int(self.landmark_list_x + self.landmark_list_width - 60),
                y=int(button_y + 25),
                width=50,
                height=50,
                on_click=lambda idx=i: self._navigate_to_landmark(idx),
                idx = i
            )
            self.navigate_buttons.append(button)
    
    def _format_landmark_name(self, destination: str) -> str:
        """
        格式化地標名稱
        例如：'Shop.tmx' -> 'Shop'
        """
        # Remove file extension
        name = destination.replace('.tmx', '')
        # Capitalize first letter
        name = name.capitalize()
        return name
    
    def _navigate_to_landmark(self, landmark_index: int):
        """開始導航到指定地標"""
        if landmark_index >= len(self.landmarks):
            Logger.warning(f"Invalid landmark index: {landmark_index}")
            return
            
        landmark_name, landmark_pos = self.landmarks[landmark_index]
        game_manager = get_game_manager()
        player = game_manager.player
        current_map = game_manager.current_map
        
        if not player or not current_map:
            Logger.warning("Cannot navigate: No player or map!")
            return
        
        # Perform A* pathfinding
        Logger.info(f"Finding path to {landmark_name}...")
        
        # Create pathfinding grid
        map_width_tiles = current_map.tmxdata.width
        map_height_tiles = current_map.tmxdata.height
        # from src.core.man

        co = [i.animation.rect for i in game_manager.enemy_trainers[game_manager.current_map_key]]
        co.extend(current_map._collision_map)
        grid = PathfindingGrid(map_width_tiles, map_height_tiles, co) 
        
        # Convert positions to tiles
        player_tile = pixel_to_tile(int(player.position.x), int(player.position.y))
        target_tile = pixel_to_tile(int(landmark_pos.x), int(landmark_pos.y))
        # print(landmark_pos, player.position)
        # print(player_tile, target_tile)
        
        Logger.info(f"Testing navigation: {player_tile} -> {target_tile}")
        # Find path
        tile_path = a_star(grid, player_tile, target_tile)
        
        if tile_path:
            # Convert back to pixel positions
            
            # Start navigation
            navigation_manager = get_navigation_manager()
            navigation_manager.start_navigation(tile_path, landmark_name)
            
            Logger.info(f"Navigation started to {landmark_name} ({len(tile_path)} waypoints)")
            
            # Close overlay
            if self.close_button and self.close_button.on_click:
                self.close_button.on_click(0)
        else:
            Logger.warning(f"No path found to {landmark_name}!")
    
    def update_content(self, dt: float):
        """更新地標按鈕"""
        for button in self.navigate_buttons:
            button.update(dt)
    
    def draw_content(self, screen: pg.Surface):
        """繪製大地圖內容"""
        # Draw title
        font_title = pg.font.Font(None, 48)
        title_text = font_title.render("Full Map", True, (0, 0, 0))
        screen.blit(title_text, (self.popup_x + self.popup_width // 2 - title_text.get_width() // 2, self.popup_y + 10))
        
        # Draw map if available
        if self.map_surface:
            # Draw border around map
            map_border = pg.Rect(
                int(self.map_display_x - 2),
                int(self.map_display_y - 2),
                self.map_surface.get_width() + 4,
                self.map_surface.get_height() + 4
            )
            pg.draw.rect(screen, (0, 0, 0), map_border, 2)
            
            # Draw map
            screen.blit(self.map_surface, (int(self.map_display_x), int(self.map_display_y)))
            
            # Draw player position (red dot)
            game_manager = get_game_manager()
            if game_manager.player:
                player_map_x = int(self.map_display_x + game_manager.player.position.x * self.map_scale)
                player_map_y = int(self.map_display_y + game_manager.player.position.y * self.map_scale)
                pg.draw.circle(screen, (255, 0, 0), (player_map_x, player_map_y), 5)
            
            # Draw landmarks (gold dots)
            for landmark_name, landmark_pos in self.landmarks:
                landmark_map_x = int(self.map_display_x + landmark_pos.x * self.map_scale)
                landmark_map_y = int(self.map_display_y + landmark_pos.y * self.map_scale)
                pg.draw.circle(screen, (255, 215, 0), (landmark_map_x, landmark_map_y), 4)
        
        # Draw landmarks list
        font_header = pg.font.Font(None, 36)
        header_text = font_header.render("Landmarks:", True, (0, 0, 0))
        screen.blit(header_text, (int(self.landmark_list_x), int(self.landmark_list_y - 40)))
        
        font_landmark = pg.font.Font(None, 28)
        for i, (landmark_name, _) in enumerate(self.landmarks):
            y_pos = self.landmark_list_y + i * 70
            
            # Draw landmark icon (gold circle)
            pg.draw.circle(screen, (255, 215, 0), (int(self.landmark_list_x + 15), int(y_pos + 35)), 8)
            
            # Draw landmark name
            landmark_text = font_landmark.render(landmark_name, True, (0, 0, 0))
            screen.blit(landmark_text, (int(self.landmark_list_x + 35), int(y_pos + 25)))
            
            # Draw navigate button
            if i < len(self.navigate_buttons):
                self.navigate_buttons[i].draw(screen)
                
                # Draw "Navigate" text on button
                nav_text = pg.font.Font(None, 18).render("Go", True, (255, 255, 255))
                button = self.navigate_buttons[i]
                screen.blit(nav_text, (button.hitbox.x + 15, button.hitbox.y + 18))
