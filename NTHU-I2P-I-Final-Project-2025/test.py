"""
TMX 地圖渲染測試
演示如何從 tileset.png 提取圖塊並根據 TMX 地圖數據渲染場景
"""

import pygame
import xml.etree.ElementTree as ET
from pathlib import Path


class TilesetLoader:
    """載入並管理 tileset"""
    
    def __init__(self, tileset_path: str, tsx_path: str):
        # 解析 TSX 文件獲取 tileset 配置
        tree = ET.parse(tsx_path)
        root = tree.getroot()
        
        self.tile_width = int(root.get('tilewidth'))
        self.tile_height = int(root.get('tileheight'))
        self.columns = int(root.get('columns'))
        self.tilecount = int(root.get('tilecount'))
        
        # 載入 tileset 圖片
        self.tileset_image = pygame.image.load(tileset_path)
        
        print(f"✓ Tileset 載入成功:")
        print(f"  - 圖塊大小: {self.tile_width}x{self.tile_height}")
        print(f"  - 每行圖塊數: {self.columns}")
        print(f"  - 總圖塊數: {self.tilecount}")
    
    def get_tile(self, tile_id: int) -> pygame.Surface:
        """根據圖塊 ID 提取對應的圖塊圖片"""
        if tile_id == 0:
            # 0 代表空白
            return None
        
        # 調整為 0-based index
        tile_id -= 1
        
        # 計算圖塊在 tileset 中的位置
        row = tile_id // self.columns
        col = tile_id % self.columns
        
        x = col * self.tile_width
        y = row * self.tile_height
        
        # 提取圖塊
        tile_surface = pygame.Surface((self.tile_width, self.tile_height), pygame.SRCALPHA)
        tile_surface.blit(self.tileset_image, (0, 0), 
                         (x, y, self.tile_width, self.tile_height))
        
        return tile_surface


class TMXMapLoader:
    """載入並渲染 TMX 地圖"""
    
    def __init__(self, tmx_path: str, tileset_loader: TilesetLoader):
        self.tileset_loader = tileset_loader
        
        # 解析 TMX 文件
        tree = ET.parse(tmx_path)
        root = tree.getroot()
        
        self.map_width = int(root.get('width'))
        self.map_height = int(root.get('height'))
        self.tile_width = int(root.get('tilewidth'))
        self.tile_height = int(root.get('tileheight'))
        
        # 載入所有圖層
        self.layers = []
        for layer in root.findall('layer'):
            layer_name = layer.get('name')
            layer_data = self._parse_layer_data(layer)
            self.layers.append({
                'name': layer_name,
                'data': layer_data
            })
        
        print(f"\n✓ 地圖載入成功:")
        print(f"  - 地圖尺寸: {self.map_width}x{self.map_height} 格")
        print(f"  - 圖層數量: {len(self.layers)}")
        print(f"  - 圖層名稱: {[layer['name'] for layer in self.layers]}")
    
    def _parse_layer_data(self, layer):
        """解析圖層的 CSV 數據"""
        data_element = layer.find('data')
        csv_data = data_element.text.strip()
        
        # 解析 CSV 為二維陣列
        rows = []
        for line in csv_data.split('\n'):
            if line.strip():
                row = [int(x) for x in line.strip().split(',')]
                rows.append(row)
        
        return rows
    
    def render(self, surface: pygame.Surface, camera_offset=(0, 0)):
        """渲染地圖到指定表面"""
        cam_x, cam_y = camera_offset
        
        # 按順序渲染每個圖層
        for layer in self.layers:
            layer_name = layer['name']
            layer_data = layer['data']
            
            # 遍歷地圖的每個格子
            for row_idx, row in enumerate(layer_data):
                for col_idx, tile_id in enumerate(row):
                    if tile_id == 0:
                        continue  # 跳過空白格子
                    
                    # 計算螢幕位置
                    x = col_idx * self.tile_width - cam_x
                    y = row_idx * self.tile_height - cam_y
                    
                    # 獲取並繪製圖塊
                    tile_surface = self.tileset_loader.get_tile(tile_id)
                    if tile_surface:
                        surface.blit(tile_surface, (x, y))


def main():
    """主程序：演示完整的地圖渲染流程"""
    
    # 初始化 Pygame
    pygame.init()
    
    # 設定視窗
    WINDOW_WIDTH = 800
    WINDOW_HEIGHT = 600
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("TMX 地圖渲染測試")
    
    # 設定路徑
    base_path = Path(__file__).parent
    tileset_png = base_path / "assets/images/tileset/tileset.png"
    tileset_tsx = base_path / "assets/maps/tileset.tsx"
    map_tmx = base_path / "assets/maps/gym.tmx"
    
    # 載入 tileset 和地圖
    print("=" * 50)
    print("開始載入資源...")
    print("=" * 50)
    
    tileset = TilesetLoader(str(tileset_png), str(tileset_tsx))
    game_map = TMXMapLoader(str(map_tmx), tileset)
    
    print("\n" + "=" * 50)
    print("資源載入完成，開始渲染...")
    print("=" * 50)
    print("\n操作說明:")
    print("  - 方向鍵: 移動視角")
    print("  - ESC: 退出")
    print("=" * 50)
    
    # 遊戲主循環
    clock = pygame.time.Clock()
    running = True
    camera_x, camera_y = 0, 0
    camera_speed = 5
    
    while running:
        # 事件處理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
        
        # 鍵盤控制相機移動
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            camera_x -= camera_speed
        if keys[pygame.K_RIGHT]:
            camera_x += camera_speed
        if keys[pygame.K_UP]:
            camera_y -= camera_speed
        if keys[pygame.K_DOWN]:
            camera_y += camera_speed
        
        # 限制相機範圍
        max_camera_x = max(0, game_map.map_width * game_map.tile_width - WINDOW_WIDTH)
        max_camera_y = max(0, game_map.map_height * game_map.tile_height - WINDOW_HEIGHT)
        camera_x = max(0, min(camera_x, max_camera_x))
        camera_y = max(0, min(camera_y, max_camera_y))
        
        # 清空螢幕
        screen.fill((0, 0, 0))
        
        # 渲染地圖
        game_map.render(screen, (camera_x, camera_y))
        
        # 顯示相機位置信息
        font = pygame.font.Font(None, 24)
        info_text = f"Camera: ({camera_x}, {camera_y})"
        text_surface = font.render(info_text, True, (255, 255, 255))
        screen.blit(text_surface, (10, 10))
        
        # 更新顯示
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    print("\n程序已退出")


if __name__ == "__main__":
    main()
