from dataclasses import dataclass

@dataclass
class Settings:
    # Screen
    SCREEN_WIDTH: int = 1280    # Width of the game window
    SCREEN_HEIGHT: int = 720    # Height of the game window
    FPS: int = 60               # Frames per second
    TITLE: str = "I2P Final"    # Title of the game window
    DEBUG: bool = True          # Debug mode
    TILE_SIZE: int = 64         # Size of each tile in pixels
    DRAW_HITBOXES: bool = True  # Draw hitboxes for debugging
    DRAW_LOS: bool = True  # Draw line of sight for debugging
    # Audio
    MAX_CHANNELS: int = 16
    AUDIO_VOLUME: float = 0.5   # Volume of audio
    # Online
    IS_ONLINE: bool = True
    ONLINE_SERVER_URL: str = "http://localhost:8989"
    MAX_MONSTERS_IN_BAG: int = 20    # Maximum number of monsters in player's bag
    

    MINIMAP_SIZE = (150, 150)        # 小地圖尺寸
    MINIMAP_VIEW_RANGE = 15          # 顯示範圍（tiles）
    MINIMAP_POSITION = (10, 10)      # 位置
    
    # Navigation
    NAV_SPEED_OPTIONS = [0.5, 1.0, 2.0, 4.0]  # 速度選項
    NAV_DEFAULT_SPEED = 1.0          # 預設速度
    NAV_PATH_COLOR = (255, 255, 0)   # 路徑顏色（黃色）
    NAV_ARRIVAL_DISTANCE = 5         # 到達判定距離（像素）

GameSettings = Settings()