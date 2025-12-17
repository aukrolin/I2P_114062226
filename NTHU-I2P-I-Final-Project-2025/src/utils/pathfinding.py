"""
Pathfinding utilities using A* algorithm for navigation system.
"""

import heapq
from typing import List, Tuple, Optional
import pygame as pg
from src.utils import GameSettings


def manhattan_distance(pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
    """
    Calculate Manhattan distance between two positions.
    Used as heuristic function for A*.
    
    Args:
        pos1: First position (x, y)
        pos2: Second position (x, y)
        
    Returns:
        Manhattan distance
    """
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
def euclidean_distance(pos1: Tuple[int, int], pos2: Tuple[int, int]) -> float:
    """
    Calculate Euclidean distance between two positions.
    Alternative heuristic for diagonal movement.
    
    Args:
        pos1: First position (x, y)
        pos2: Second position (x, y)
        
    Returns:
        Euclidean distance
    """
    dx = pos1[0] - pos2[0]
    dy = pos1[1] - pos2[1]
    return (dx * dx + dy * dy) ** 0.5


class PathfindingGrid:
    """
    Tile-based grid for pathfinding.
    Precomputes walkable/non-walkable tiles from collision map.
    """
    
    def __init__(self, map_width_tiles: int, map_height_tiles: int, collision_map: list[pg.Rect]):
        """
        Initialize pathfinding grid.
        
        Args:
            map_width_tiles: Width of map in tiles
            map_height_tiles: Height of map in tiles
            collision_map: List of collision rectangles (in pixels)
        """
        self.width = map_width_tiles
        self.height = map_height_tiles
        
        # Initialize all tiles as walkable
        self.grid = [[True] * map_width_tiles for _ in range(map_height_tiles)]
        
        # Mark collision tiles as non-walkable
        for rect in collision_map:
            # Convert pixel coordinates to tile coordinates
            tile_x = rect.x // GameSettings.TILE_SIZE
            tile_y = rect.y // GameSettings.TILE_SIZE
            
            # Handle collision rects that span multiple tiles
            tile_width = max(1, rect.width // GameSettings.TILE_SIZE)
            tile_height = max(1, rect.height // GameSettings.TILE_SIZE)
            
            for dy in range(tile_height):
                for dx in range(tile_width):
                    tx = tile_x + dx
                    ty = tile_y + dy
                    if 0 <= tx < map_width_tiles and 0 <= ty < map_height_tiles:
                        self.grid[ty][tx] = False
    
    def is_walkable(self, tile_x: int, tile_y: int) -> bool:
        """
        Check if a tile is walkable.
        
        Args:
            tile_x: X coordinate in tiles
            tile_y: Y coordinate in tiles
            
        Returns:
            True if tile is walkable, False otherwise
        """
        if 0 <= tile_x < self.width and 0 <= tile_y < self.height:
            return self.grid[tile_y][tile_x]
        return False
    
    def get_neighbors(self, tile_x: int, tile_y: int, allow_diagonal: bool = True) -> List[Tuple[int, int]]:
        """
        Get walkable neighboring tiles.
        
        Args:
            tile_x: X coordinate in tiles
            tile_y: Y coordinate in tiles
            allow_diagonal: If True, include diagonal neighbors
            
        Returns:
            List of (x, y) tuples for walkable neighbors
        """
        # Four cardinal directions
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        
        if allow_diagonal:
            # Add diagonal directions
            directions.extend([(1, 1), (1, -1), (-1, 1), (-1, -1)])
        
        neighbors = []
        for dx, dy in directions:
            nx, ny = tile_x + dx, tile_y + dy
            if self.is_walkable(nx, ny):
                neighbors.append((nx, ny))
        
        return neighbors




def a_star(grid: PathfindingGrid, 
           start: Tuple[int, int], 
           goal: Tuple[int, int],
           allow_diagonal: bool = False) -> Optional[List[Tuple[int, int]]]:
    """
    A* pathfinding algorithm.
    
    Args:
        grid: PathfindingGrid instance
        start: Starting position (tile_x, tile_y)
        goal: Goal position (tile_x, tile_y)
        allow_diagonal: If True, allow diagonal movement
        
    Returns:
        List of (tile_x, tile_y) positions representing the path,
        or None if no path exists.
        The path includes both start and goal positions.
    """
    # Check if start and goal are walkable
    if not grid.is_walkable(*start):
        print(f"[A*] Start position {start} is not walkable")
        return None
    
    if not grid.is_walkable(*goal):
        print(f"[A*] Goal position {goal} is not walkable")
        return None
    
    # If start == goal, return single-point path
    if start == goal:
        return [start]
    
    # Priority queue: (f_score, counter, node)
    # counter ensures stable sorting when f_scores are equal
    counter = 0
    open_set = [(0, counter, start)]
    
    # Track where each node came from
    came_from = {}
    
    # Cost from start to each node
    g_score = {start: 0}
    
    # Estimated total cost (g_score + heuristic)
    f_score = {start: manhattan_distance(start, goal)}
    
    # Nodes in open set (for fast membership check)
    open_set_hash = {start}
    
    while open_set:
        _, _, current = heapq.heappop(open_set)
        open_set_hash.discard(current)
        
        # Check if we reached the goal
        if current == goal:
            # Reconstruct path
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            return path[::-1]  # Reverse to get start->goal order
        
        # Explore neighbors
        for neighbor in grid.get_neighbors(*current, allow_diagonal=allow_diagonal):
            # Calculate cost to reach neighbor
            # Diagonal moves cost sqrt(2) ≈ 1.414, cardinal moves cost 1
            if allow_diagonal:
                dx = abs(neighbor[0] - current[0])
                dy = abs(neighbor[1] - current[1])
                move_cost = 1.414 if (dx + dy) == 2 else 1.0
            else:
                move_cost = 1
            
            tentative_g_score = g_score[current] + move_cost
            
            # If this is a better path to neighbor, update it
            if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f = tentative_g_score + manhattan_distance(neighbor, goal)
                f_score[neighbor] = f
                
                # Add to open set if not already there
                if neighbor not in open_set_hash:
                    counter += 1
                    heapq.heappush(open_set, (f, counter, neighbor))
                    open_set_hash.add(neighbor)
    
    # No path found
    print(f"[A*] No path found from {start} to {goal}")
    return None

def smooth_path(path: List[Tuple[int, int]], grid: PathfindingGrid) -> List[Tuple[int, int]]:
    """
    Smooth a path by removing unnecessary waypoints.
    Uses line-of-sight checks to skip intermediate points.
    
    Args:
        path: Original path as list of (tile_x, tile_y)
        grid: PathfindingGrid for collision checking
        
    Returns:
        Smoothed path with fewer waypoints
    """
    if len(path) <= 2:
        return path
    
    smoothed = [path[0]]
    current_idx = 0
    
    while current_idx < len(path) - 1:
        # Try to skip as many points as possible
        farthest_idx = current_idx + 1
        
        for test_idx in range(current_idx + 2, len(path)):
            if has_line_of_sight(path[current_idx], path[test_idx], grid):
                farthest_idx = test_idx
            else:
                break
        
        smoothed.append(path[farthest_idx])
        current_idx = farthest_idx
    
    return smoothed

def has_line_of_sight(start: Tuple[int, int], end: Tuple[int, int], grid: PathfindingGrid) -> bool:
    """
    Check if there's a clear line of sight between two tiles.
    Uses Bresenham's line algorithm.
    
    Args:
        start: Starting tile (tile_x, tile_y)
        end: Ending tile (tile_x, tile_y)
        grid: PathfindingGrid for collision checking
        
    Returns:
        True if line of sight is clear, False otherwise
    """
    x0, y0 = start
    x1, y1 = end
    
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    
    x_step = 1 if x0 < x1 else -1
    y_step = 1 if y0 < y1 else -1
    
    error = dx - dy
    
    x, y = x0, y0
    
    while True:
        # Check if current tile is walkable
        if not grid.is_walkable(x, y):
            return False
        
        if x == x1 and y == y1:
            break
        
        e2 = 2 * error
        
        if e2 > -dy:
            error -= dy
            x += x_step
        
        if e2 < dx:
            error += dx
            y += y_step
    
    return True
