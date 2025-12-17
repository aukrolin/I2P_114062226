"""
Minimap component for displaying player's surroundings.
Shows player position, other players, NPCs, and landmarks.
"""

import pygame as pg
from typing import List, Tuple, Optional
from src.utils import GameSettings, Position


class Minimap:
    """
    常態小地圖 - 顯示玩家周圍區域
    """
    
    def __init__(self, size: Tuple[int, int] = None, view_range: int = None, position: Tuple[int, int] = None, update_rate: float = 4.0):
        """
        Initialize minimap.
        
        Args:
            size: Minimap size in pixels (width, height). Defaults to MINIMAP_SIZE from settings.
            view_range: View range in tiles. Defaults to MINIMAP_VIEW_RANGE from settings.
            position: Screen position (x, y). Defaults to MINIMAP_POSITION from settings.
            update_rate: Updates per second (default 4 = every 0.25s)
        """
        self.size = size or GameSettings.MINIMAP_SIZE
        self.view_range = view_range or GameSettings.MINIMAP_VIEW_RANGE
        self.position = position or GameSettings.MINIMAP_POSITION
        self.update_rate = update_rate
        self.update_interval = 1.0 / update_rate
        self.time_since_update = 0.0
        
        # Create surface for minimap (cache rendered result)
        self.surface = pg.Surface(self.size, pg.SRCALPHA)
        self.needs_update = True  # Force first update
        
        # Colors
        self.bg_color = (0, 0, 0, 180)  # Semi-transparent black
        self.border_color = (255, 255, 255)
        self.walkable_color = (100, 100, 100)  # Gray for walkable tiles
        self.collision_color = (40, 40, 40)  # Dark gray for collision
        self.player_color = (255, 0, 0)  # Red for player
        self.other_player_color = (0, 150, 255)  # Blue for other players
        self.npc_color = (0, 255, 0)  # Green for NPCs
        self.landmark_color = (255, 215, 0)  # Gold for landmarks
        
        # Marker sizes
        self.player_radius = 4
        self.other_player_radius = 3
        self.npc_radius = 3
        self.landmark_radius = 4
        
        # Border
        self.border_width = 2
    
    def update(self, dt: float):
        """
        Update minimap timer.
        
        Args:
            dt: Delta time in seconds
        """
        self.time_since_update += dt
        if self.time_since_update >= self.update_interval:
            self.needs_update = True
            self.time_since_update = 0.0
    
    def draw(self, screen: pg.Surface, player_pos: Position, 
             collision_map: List[pg.Rect],
             other_players: List[dict] = None,
             npcs: List[dict] = None,
             teleporters: List = None,
             current_map_name: str = None):
        """
        Draw minimap on screen. Only re-renders when update interval passed.
        
        Args:
            screen: Screen surface to draw on
            player_pos: Player's current position (pixel coordinates)
            collision_map: List of collision rectangles
            other_players: List of other player dicts with 'x', 'y', 'map' keys
            npcs: List of NPC dicts with 'x', 'y' keys
            teleporters: List of Teleport objects
            current_map_name: Current map name (for filtering other players)
        """
        # Only re-render if update is needed
        if not self.needs_update:
            # Just blit cached surface
            screen.blit(self.surface, self.position)
            return
        
        # Mark as updated
        self.needs_update = False
        
        # Clear surface
        self.surface.fill(self.bg_color)
        
        # Calculate tiles per pixel ratio
        tiles_per_pixel = self.view_range * 2 / min(self.size)
        pixel_size = min(self.size) / (self.view_range * 2)
        
        # Player's tile position (center of view)
        player_tile_x = int(player_pos.x // GameSettings.TILE_SIZE)
        player_tile_y = int(player_pos.y // GameSettings.TILE_SIZE)
        
        # Calculate view bounds in tiles
        min_tile_x = player_tile_x - self.view_range
        max_tile_x = player_tile_x + self.view_range
        min_tile_y = player_tile_y - self.view_range
        max_tile_y = player_tile_y + self.view_range
        
        # Draw tiles
        for tile_y in range(min_tile_y, max_tile_y + 1):
            for tile_x in range(min_tile_x, max_tile_x + 1):
                # Calculate screen position on minimap
                screen_x = int((tile_x - min_tile_x) * pixel_size)
                screen_y = int((tile_y - min_tile_y) * pixel_size)
                
                if screen_x >= self.size[0] or screen_y >= self.size[1]:
                    continue
                
                # Check if tile has collision
                tile_rect = pg.Rect(
                    tile_x * GameSettings.TILE_SIZE,
                    tile_y * GameSettings.TILE_SIZE,
                    GameSettings.TILE_SIZE,
                    GameSettings.TILE_SIZE
                )
                
                has_collision = any(tile_rect.colliderect(r) for r in collision_map)
                color = self.collision_color if has_collision else self.walkable_color
                
                # Draw tile (small rectangle)
                tile_size = max(1, int(pixel_size))
                pg.draw.rect(self.surface, color, 
                           (screen_x, screen_y, tile_size, tile_size))
        
        # Draw teleporters/landmarks
        if teleporters:
            for tp in teleporters:
                tp_tile_x = int(tp.pos.x // GameSettings.TILE_SIZE)
                tp_tile_y = int(tp.pos.y // GameSettings.TILE_SIZE)
                
                # Check if in view range
                if (min_tile_x <= tp_tile_x <= max_tile_x and 
                    min_tile_y <= tp_tile_y <= max_tile_y):
                    screen_x = int((tp_tile_x - min_tile_x) * pixel_size)
                    screen_y = int((tp_tile_y - min_tile_y) * pixel_size)
                    
                    # Draw landmark marker
                    pg.draw.circle(self.surface, self.landmark_color, 
                                 (screen_x + int(pixel_size/2), screen_y + int(pixel_size/2)), 
                                 self.landmark_radius)
        
        # Draw NPCs
        if npcs:
            for npc in npcs:
                npc_tile_x = int(npc.get('x', 0) // GameSettings.TILE_SIZE)
                npc_tile_y = int(npc.get('y', 0) // GameSettings.TILE_SIZE)
                
                # Check if in view range
                if (min_tile_x <= npc_tile_x <= max_tile_x and 
                    min_tile_y <= npc_tile_y <= max_tile_y):
                    screen_x = int((npc_tile_x - min_tile_x) * pixel_size)
                    screen_y = int((npc_tile_y - min_tile_y) * pixel_size)
                    
                    # Draw NPC marker
                    pg.draw.circle(self.surface, self.npc_color, 
                                 (screen_x + int(pixel_size/2), screen_y + int(pixel_size/2)), 
                                 self.npc_radius)
        
        # Draw other players (only those on same map)
        if other_players and current_map_name:
            for p in other_players:
                # Filter by map
                if p.get('map') != current_map_name:
                    continue
                
                p_tile_x = int(p.get('x', 0) // GameSettings.TILE_SIZE)
                p_tile_y = int(p.get('y', 0) // GameSettings.TILE_SIZE)
                
                # Check if in view range
                if (min_tile_x <= p_tile_x <= max_tile_x and 
                    min_tile_y <= p_tile_y <= max_tile_y):
                    screen_x = int((p_tile_x - min_tile_x) * pixel_size)
                    screen_y = int((p_tile_y - min_tile_y) * pixel_size)
                    
                    # Draw other player marker
                    pg.draw.circle(self.surface, self.other_player_color, 
                                 (screen_x + int(pixel_size/2), screen_y + int(pixel_size/2)), 
                                 self.other_player_radius)
        
        # Draw player (always at center)
        center_x = self.size[0] // 2
        center_y = self.size[1] // 2
        pg.draw.circle(self.surface, self.player_color, 
                     (center_x, center_y), self.player_radius)
        
        # Draw border
        pg.draw.rect(self.surface, self.border_color, 
                   (0, 0, self.size[0], self.size[1]), self.border_width)
        
        # Blit to screen
        screen.blit(self.surface, self.position)
    
    def draw_navigation_path(self, screen: pg.Surface, player_pos: Position, 
                            path: List[Tuple[int, int]]):
        """
        Draw navigation path on minimap.
        
        Args:
            screen: Screen surface (not used, draws on self.surface)
            player_pos: Player's current position (pixel coordinates)
            path: List of (tile_x, tile_y) tuples representing the path
        """
        if not path or len(path) < 2:
            return
        
        # Calculate tiles per pixel ratio
        pixel_size = min(self.size) / (self.view_range * 2)
        
        # Player's tile position (center of view)
        player_tile_x = int(player_pos.x // GameSettings.TILE_SIZE)
        player_tile_y = int(player_pos.y // GameSettings.TILE_SIZE)
        
        # Calculate view bounds in tiles
        min_tile_x = player_tile_x - self.view_range
        min_tile_y = player_tile_y - self.view_range
        
        # Draw path lines
        prev_screen_pos = None
        for tile_x, tile_y in path:
            # Check if in view range
            if (abs(tile_x - player_tile_x) <= self.view_range and 
                abs(tile_y - player_tile_y) <= self.view_range):
                
                screen_x = int((tile_x - min_tile_x) * pixel_size + pixel_size/2)
                screen_y = int((tile_y - min_tile_y) * pixel_size + pixel_size/2)
                
                if prev_screen_pos:
                    pg.draw.line(self.surface, GameSettings.NAV_PATH_COLOR,
                               prev_screen_pos, (screen_x, screen_y), 2)
                
                prev_screen_pos = (screen_x, screen_y)
