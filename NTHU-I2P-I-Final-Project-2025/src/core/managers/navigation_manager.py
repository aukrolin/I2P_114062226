"""
Navigation Manager for automatic player movement.
Handles path following, speed control, and navigation state.
"""

from typing import List, Tuple, Optional, TYPE_CHECKING
from src.utils import GameSettings, Position, Logger
# from src.core.managers.game_manager import GameManager
if TYPE_CHECKING:
    from src.entities import Player


class NavigationManager:
    """
    管理自動導航狀態和玩家移動
    """
    
    def __init__(self):
        """Initialize navigation manager."""
        self.active = False
        self.path: List[Tuple[int, int]] = []  # List of (pixel_x, pixel_y)
        self.current_index = 0
        self.target_name = ""
        
        # Speed control
        self.speed_options = GameSettings.NAV_SPEED_OPTIONS  # [0.5, 1.0, 2.0, 4.0]
        self.speed_index = 1  # Default to 1.0x
        self.speed_multiplier = self.speed_options[self.speed_index]
        
        # Arrival detection
        self.arrival_distance = GameSettings.NAV_ARRIVAL_DISTANCE
        
        # Stuck detection
        self.stuck_counter = 0
        self.stuck_threshold = 60  # 1 second at 60fps
        self.last_distance = float('inf')
        
        Logger.info("NavigationManager initialized")
    
    def start_navigation(self, path: List[Tuple[int, int]], target_name: str = "destination"):
        """
        開始導航到目標點
        
        Args:
            path: List of (pixel_x, pixel_y) waypoints
            target_name: Name of the destination (for display)
        """
        if not path or len(path) < 2:
            Logger.warning(f"Cannot start navigation: invalid path (length={len(path) if path else 0})")
            return False
        
        self.active = True
        self.path = path
        self.current_index = 0
        self.target_name = target_name
        
        Logger.info(f"Navigation started to '{target_name}' ({len(path)} waypoints, speed={self.speed_multiplier}x)")
        Logger.info(f"waypoints: {self.path}")
        return True
    
    def cancel(self):
        """取消當前導航"""
        if self.active:
            Logger.info(f"Navigation to '{self.target_name}' cancelled")
        
        self.active = False
        self.path = []
        self.current_index = 0
        self.target_name = ""
        self.speed_index = 1
        self.speed_multiplier = self.speed_options[self.speed_index]
        self.stuck_counter = 0
        self.last_distance = float('inf')
    
    def toggle_speed(self):
        """
        切換導航速度 [0.5x, 1x, 2x, 4x]
        循環切換到下一個速度
        """
        self.speed_index = (self.speed_index + 1) % len(self.speed_options)
        self.speed_multiplier = self.speed_options[self.speed_index]
        
        Logger.info(f"Navigation speed: {self.speed_multiplier}x")
        return self.speed_multiplier
    
    def set_speed(self, multiplier: float):
        """
        直接設置導航速度
        
        Args:
            multiplier: Speed multiplier (0.5, 1.0, 2.0, 4.0, etc.)
        """
        if multiplier in self.speed_options:
            self.speed_multiplier = multiplier
            self.speed_index = self.speed_options.index(multiplier)
            Logger.info(f"Navigation speed set to: {self.speed_multiplier}x")
        else:
            Logger.warning(f"Invalid speed multiplier: {multiplier}")
    
    def update(self, player: "Player", dt: float) -> bool:
        """
        更新導航狀態，自動移動玩家
        
        Args:
            player: Player entity to move
            dt: Delta time (not used, player handles its own dt)
            
        Returns:
            True if navigation is active, False if finished/inactive
        """
        if not self.active or not self.path:
            return False
        
        # Check if we've reached the end
        if self.current_index >= len(self.path):
            Logger.info(f"Arrived at '{self.target_name}'")
            self.active = False
            return False
        
        # Get current target waypoint
        target_x, target_y = self.path[self.current_index]
        
        import math
        


        
        target_pixel_x = target_x * GameSettings.TILE_SIZE
        target_pixel_y = target_y * GameSettings.TILE_SIZE
        precise_dx = target_pixel_x - player.position.x
        precise_dy = target_pixel_y - player.position.y
        precise_distance = math.hypot(precise_dx, precise_dy)
        
        # Check if reached current waypoint (within 5 pixels of tile center)
        if precise_distance < GameSettings.NAV_ARRIVAL_DISTANCE:
            Logger.info(f"Reached waypoint {self.current_index} (precise_distance={precise_distance:.1f}px)")
            player.position.x = target_pixel_x
            player.position.y = target_pixel_y
            self.current_index += 1
            self.stuck_counter = 0
            self.last_distance = float('inf')
            
            # Check if this was the last waypoint
            if self.current_index >= len(self.path):
                Logger.info(f"Arrived at '{self.target_name}'")
                self.active = False
                return False
            
            # Move to next waypoint
            return True
        
        # Stuck detection
        if precise_distance >= self.last_distance - 0.1:  # Not making progress
            self.stuck_counter += 1
        else:
            self.stuck_counter = 0  # Reset counter if making progress
        
        self.last_distance = precise_distance
        
        # Move player towards tile center
        if precise_distance > 0:
            # Normalize direction
            direction_x = precise_dx / precise_distance
            direction_y = precise_dy / precise_distance
            
            # Clean up floating point errors (< 0.001 treated as 0)
            if abs(direction_x) < 0.001:
                direction_x = 0.0
            if abs(direction_y) < 0.001:
                direction_y = 0.0
            
            player.automove(direction_x * self.speed_multiplier, direction_y * self.speed_multiplier)
        
        return True
    
    def get_status(self) -> dict:
        """
        獲取當前導航狀態信息
        
        Returns:
            Dict with status info
        """
        return {
            'active': self.active,
            'target': self.target_name,
            'progress': f"{self.current_index}/{len(self.path)}" if self.path else "0/0",
            'speed': f"{self.speed_multiplier}x",
            'waypoints_remaining': len(self.path) - self.current_index if self.path else 0
        }
    
    def get_remaining_path(self) -> List[Tuple[int, int]]:
        """
        獲取剩餘的路徑點（用於在小地圖上顯示）
        
        Returns:
            List of remaining (pixel_x, pixel_y) waypoints
        """
        if not self.active or not self.path:
            return []
        
        return self.path[self.current_index:]
