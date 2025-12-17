# Minimap & Navigation 系統設計文檔

## 📋 需求總覽

### Minimap (2分)
- 常態小地圖：顯示玩家周圍區域
- 大地圖模式：全螢幕顯示整個地圖

### Navigation (4分)
- 地點列表與導航按鈕
- A* 路徑尋找
- 自動導航功能
- ESC 取消導航

---

## 🗺️ Minimap 系統詳細設計

### 模式 1：常態小地圖（左上角）

#### 顯示規格
- **位置**：螢幕左上角固定位置
- **尺寸**：150×150 像素（可配置）
- **顯示範圍**：玩家周圍 15×15 tiles（可配置參數）
  ```python
  # settings.py 或 GameSettings
  MINIMAP_SIZE = (150, 150)
  MINIMAP_VIEW_RANGE = 15  # tiles，可輕鬆調整
  ```

#### 元素標記
- 🔴 **紅點** = 當前玩家位置（中心點）
- 🔵 **藍點** = 其他線上玩家（from `online_manager.list_players`）
- 🟢 **綠點** = NPC Trainer（from map enemy_trainers）
- 🏛️ **Icon** = 地標（teleporter locations）
- ⬛ **灰色/黑色** = 碰撞區域（collision tiles）
- ⬜ **白色/淺色** = 可行走區域

#### 實作細節
```python
class Minimap:
    def __init__(self, size=(150, 150), view_range=15):
        self.size = size
        self.view_range = view_range
        self.position = (10, 10)  # 左上角偏移
        
    def draw(self, screen, player_pos, map_data, 
             other_players, npcs, teleporters):
        # 1. 計算顯示範圍（player_pos 為中心）
        # 2. 渲染該範圍的地圖縮略圖
        # 3. 繪製碰撞區域（灰色小方塊）
        # 4. 繪製標記點：
        #    - 玩家（紅點，中心）
        #    - 其他玩家（藍點）
        #    - NPC（綠點）
        #    - Teleporter（圖標）
```

---

### 模式 2：大地圖模式（全螢幕）

#### 觸發方式
- **UI 按鈕**：放在右下角，與 Bag/Settings 並排
  ```
  ┌─────┬──────────┬─────┬─────┐
  │ Bag │ Settings │ Map │  ?  │
  └─────┴──────────┴─────┴─────┘
  ```

#### 顯示方式
- **選項 A**：Overlay（推薦）
  - 半透明黑色背景遮罩
  - 中間顯示完整地圖縮小版
  - 右側列表顯示地標按鈕

- **選項 B**：新 Scene
  - 完全獨立的 `MapScene`
  - 優點：更乾淨的架構
  - 缺點：需要保存 game_scene 狀態

#### 大地圖內容
```
┌────────────────────────────────────────┐
│  [X] Close          Full Map           │
│                                        │
│  ┌──────────────┐  ┌──────────────┐  │
│  │              │  │  Landmarks:   │  │
│  │              │  │               │  │
│  │   整個地圖    │  │ 🏛️ Shop      │  │
│  │   縮小版     │  │   [Navigate] │  │
│  │              │  │               │  │
│  │  🔴🔵🟢      │  │ 🏛️ Gym       │  │
│  │              │  │   [Navigate] │  │
│  └──────────────┘  │               │  │
│                    │ 🏛️ PokéCenter│  │
│                    │   [Navigate] │  │
│                    └──────────────┘  │
└────────────────────────────────────────┘
```

#### 地標定義
- **來源**：只使用現有的 `teleporters` 列表
- **顯示名稱**：從 teleporter 的目標地圖名稱推導
  - `Shop.tmx` → "Shop"
  - `gym.tmx` → "Gym"
  - 或添加 `display_name` 屬性到 Teleport 類別

---

## 🧭 Navigation 系統詳細設計

### 導航流程
```
1. 玩家點擊右下角 Map 按鈕
   ↓
2. 顯示大地圖 Overlay/Scene
   ↓
3. 玩家點擊某個地標的 [Navigate] 按鈕
   ↓
4. 執行 A* 尋路（start=玩家位置, goal=地標位置）
   ↓
5. 關閉大地圖
   ↓
6. 開始自動導航（NavigationManager.start()）
   ↓
7. 玩家自動沿路徑移動
   ↓
8. 到達目標 或 按 ESC 取消
```

---

### A* 路徑尋找實作

#### 建圖方式

**方案 A：Tile-based Grid（推薦）**
```python
class PathfindingGrid:
    def __init__(self, map_width_tiles, map_height_tiles, collision_map):
        # 建立 2D grid：grid[y][x] = walkable (True/False)
        self.width = map_width_tiles
        self.height = map_height_tiles
        self.grid = [[True] * map_width_tiles for _ in range(map_height_tiles)]
        
        # 根據 collision_map 標記不可行走的 tiles
        for rect in collision_map:
            tile_x = rect.x // TILE_SIZE
            tile_y = rect.y // TILE_SIZE
            if 0 <= tile_x < map_width_tiles and 0 <= tile_y < map_height_tiles:
                self.grid[tile_y][tile_x] = False
    
    def is_walkable(self, tile_x, tile_y):
        if 0 <= tile_x < self.width and 0 <= tile_y < self.height:
            return self.grid[tile_y][tile_x]
        return False
    
    def get_neighbors(self, tile_x, tile_y):
        # 四方向移動（或八方向）
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        neighbors = []
        for dx, dy in directions:
            nx, ny = tile_x + dx, tile_y + dy
            if self.is_walkable(nx, ny):
                neighbors.append((nx, ny))
        return neighbors
```

**方案 B：Direct Collision Check（簡單但較慢）**
```python
def get_neighbors(pos: Position, collision_map):
    # 直接檢查四個方向是否碰撞
    directions = [(0, TILE_SIZE), (TILE_SIZE, 0), 
                  (0, -TILE_SIZE), (-TILE_SIZE, 0)]
    neighbors = []
    for dx, dy in directions:
        new_pos = Position(pos.x + dx, pos.y + dy)
        rect = create_rect_at(new_pos)
        if not any(rect.colliderect(r) for r in collision_map):
            neighbors.append(new_pos)
    return neighbors
```

**推薦：方案 A**
- 優點：預先建圖，A* 執行快
- 缺點：初始化需要遍歷所有 tiles
- 適用：地圖不會動態改變的情況

---

#### A* 演算法實作

```python
import heapq
from typing import List, Tuple, Optional

def manhattan_distance(pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
    """曼哈頓距離作為啟發式函數"""
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

def a_star(grid: PathfindingGrid, 
           start: Tuple[int, int], 
           goal: Tuple[int, int]) -> Optional[List[Tuple[int, int]]]:
    """
    A* 路徑尋找
    
    Args:
        grid: PathfindingGrid 實例
        start: 起點 (tile_x, tile_y)
        goal: 終點 (tile_x, tile_y)
    
    Returns:
        路徑列表 [(x1,y1), (x2,y2), ...] 或 None（無路徑）
    """
    if not grid.is_walkable(*start) or not grid.is_walkable(*goal):
        return None
    
    # Priority queue: (f_score, counter, node)
    counter = 0
    open_set = [(0, counter, start)]
    came_from = {}
    
    g_score = {start: 0}
    f_score = {start: manhattan_distance(start, goal)}
    
    while open_set:
        _, _, current = heapq.heappop(open_set)
        
        if current == goal:
            # 重建路徑
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            return path[::-1]  # 反轉
        
        for neighbor in grid.get_neighbors(*current):
            tentative_g = g_score[current] + 1  # 每步成本為 1
            
            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f = tentative_g + manhattan_distance(neighbor, goal)
                f_score[neighbor] = f
                
                counter += 1
                heapq.heappush(open_set, (f, counter, neighbor))
    
    return None  # 無法到達

# 使用範例
def find_path_to_landmark(player_pos: Position, landmark_pos: Position, 
                          collision_map: list[pg.Rect]) -> List[Position]:
    """將像素座標轉換為 tile 並執行 A*"""
    grid = PathfindingGrid(map_width_tiles, map_height_tiles, collision_map)
    
    start_tile = (player_pos.x // TILE_SIZE, player_pos.y // TILE_SIZE)
    goal_tile = (landmark_pos.x // TILE_SIZE, landmark_pos.y // TILE_SIZE)
    
    tile_path = a_star(grid, start_tile, goal_tile)
    
    if tile_path:
        # 轉回像素座標
        return [Position(x * TILE_SIZE, y * TILE_SIZE) for x, y in tile_path]
    return []
```

---

### 自動導航實作

#### NavigationManager

```python
class NavigationManager:
    """管理導航狀態和自動移動"""
    
    def __init__(self):
        self.active = False
        self.path: List[Position] = []
        self.current_index = 0
        self.target_name = ""
        self.speed_multiplier = 1.0  # [0.5, 1, 2, 4] 可切換
        self.speed_options = [0.5, 1.0, 2.0, 4.0]
        self.speed_index = 1  # 預設 1.0x
    
    def start_navigation(self, path: List[Position], target_name: str):
        """開始導航"""
        self.active = True
        self.path = path
        self.current_index = 0
        self.target_name = target_name
        Logger.info(f"Navigation started to {target_name}")
    
    def cancel(self):
        """取消導航"""
        self.active = False
        self.path = []
        self.current_index = 0
        Logger.info("Navigation cancelled")
    
    def toggle_speed(self):
        """切換速度 [0.5x, 1x, 2x, 4x]"""
        self.speed_index = (self.speed_index + 1) % len(self.speed_options)
        self.speed_multiplier = self.speed_options[self.speed_index]
        Logger.info(f"Navigation speed: {self.speed_multiplier}x")
    
    def update(self, player: Player, dt: float):
        """更新導航狀態，自動移動玩家"""
        if not self.active or not self.path:
            return
        
        if self.current_index >= len(self.path):
            # 到達終點
            Logger.info(f"Arrived at {self.target_name}")
            self.active = False
            return
        
        target_pos = self.path[self.current_index]
        
        # 計算方向
        dx = target_pos.x - player.position.x
        dy = target_pos.y - player.position.y
        distance = (dx**2 + dy**2) ** 0.5
        
        if distance < 5:  # 到達當前路徑點
            self.current_index += 1
            return
        
        # 移動玩家（應用速度倍率）
        move_speed = player.speed * self.speed_multiplier
        if abs(dx) > abs(dy):
            player.move_direction = Direction.RIGHT if dx > 0 else Direction.LEFT
            player.velocity.x = move_speed if dx > 0 else -move_speed
        else:
            player.move_direction = Direction.DOWN if dy > 0 else Direction.UP
            player.velocity.y = move_speed if dy > 0 else -move_speed
    
    def draw_path(self, screen: pg.Surface, camera: PositionCamera):
        """在小地圖上繪製路徑（可選）"""
        if not self.active or len(self.path) < 2:
            return
        
        for i in range(len(self.path) - 1):
            start = camera.transform_position(self.path[i])
            end = camera.transform_position(self.path[i + 1])
            pg.draw.line(screen, (255, 255, 0), 
                        (start.x, start.y), (end.x, end.y), 2)
```

---

### 取消導航機制

#### 觸發條件
1. **按下 ESC 鍵**
   ```python
   if input_manager.key_pressed(pg.K_ESCAPE) and navigation_manager.active:
       navigation_manager.cancel()
   ```

2. **玩家手動移動**（可選）
   ```python
   if (input_manager.key_held(pg.K_w) or 
       input_manager.key_held(pg.K_a) or 
       input_manager.key_held(pg.K_s) or 
       input_manager.key_held(pg.K_d)):
       if navigation_manager.active:
           navigation_manager.cancel()
   ```

3. **到達目標**
   - 自動停止

---

## 🎨 UI/UX 設計

### 常態小地圖 UI
```
位置：左上角 (10, 10)
尺寸：150×150 px
邊框：2px 白色
背景：半透明黑色

┌──────────────┐
│🟩🟦⬜⬜⬜⬜⬜⬜│
│⬜🟢⬜⬛⬛⬜⬜⬜│
│⬜⬜🔴⬜⬜⬜⬜🏛️│ ← 🔴 玩家居中
│⬜⬜⬜🔵⬜⬜⬜⬜│
│⬜⬜⬜⬜⬛⬜⬜⬜│
└──────────────┘
```

### 大地圖按鈕
```
位置：右下角
尺寸：60×60 px
圖示：地圖 icon
```

### 導航速度顯示
```
導航中顯示：
┌─────────────────┐
│ → Shop  [2.0x]  │ ← 左上角通知
└─────────────────┘

點擊通知或按 N 鍵切換速度
```

---

## 📁 文件結構

```
src/
├── interface/
│   └── components/
│       ├── minimap.py              # 常態小地圖
│       └── map_button.py           # 地圖按鈕
│
├── overlay/
│   └── fullmap_overlay.py          # 大地圖 overlay
│   （或）
├── scenes/
│   └── map_scene.py                # 大地圖 scene（可選）
│
├── utils/
│   └── pathfinding.py              # A* 演算法
│       ├── PathfindingGrid
│       ├── a_star()
│       └── manhattan_distance()
│
└── core/
    └── managers/
        └── navigation_manager.py    # 導航管理器
```

---

## 🔧 配置參數

### GameSettings 新增項目
```python
# settings.py
class GameSettings:
    # ... 現有設定
    
    # Minimap
    MINIMAP_SIZE = (150, 150)        # 小地圖尺寸
    MINIMAP_VIEW_RANGE = 15          # 顯示範圍（tiles）
    MINIMAP_POSITION = (10, 10)      # 位置
    
    # Navigation
    NAV_SPEED_OPTIONS = [0.5, 1.0, 2.0, 4.0]  # 速度選項
    NAV_DEFAULT_SPEED = 1.0          # 預設速度
    NAV_PATH_COLOR = (255, 255, 0)   # 路徑顏色（黃色）
    NAV_ARRIVAL_DISTANCE = 5         # 到達判定距離（像素）
```

---

## 🚀 實作順序

### Phase 1: 路徑尋找核心
1. ✅ 實作 `pathfinding.py`
   - PathfindingGrid 類別
   - A* 演算法
   - 測試用例

### Phase 2: 常態小地圖
2. ✅ 實作 `minimap.py`
   - 繪製周圍區域
   - 標記玩家、NPC、其他玩家
3. ✅ 整合到 `game_scene.py`

### Phase 3: 導航管理器
4. ✅ 實作 `navigation_manager.py`
   - 路徑追蹤
   - 自動移動
   - 速度切換
5. ✅ 整合到 `game_scene.py`
6. ✅ 實作 ESC 取消

### Phase 4: 大地圖 UI
7. ✅ 實作地圖按鈕
8. ✅ 實作 `fullmap_overlay.py` 或 `map_scene.py`
   - 顯示完整地圖
   - 地標列表
   - Navigate 按鈕
9. ✅ 連接導航功能

### Phase 5: 優化與測試
10. ✅ 路徑平滑化（可選）
11. ✅ 性能優化
12. ✅ 完整測試

---

## 📊 A* 建圖詳細討論

### 建圖時機
- **初始化時**：Map 載入時建立 PathfindingGrid
- **快取**：Grid 建好後不需要每次重建
- **更新**：地圖不會動態改變，無需更新

### 記憶體消耗
假設地圖 100×100 tiles：
```python
grid = 100 × 100 × 1 byte (bool) = 10,000 bytes ≈ 10 KB
```
非常小，完全可接受。

### 複雜度分析
- **建圖**：O(W × H) 其中 W, H 是地圖寬高（tiles）
- **A* 搜尋**：O((W × H) log(W × H)) 最壞情況
- **實際**：通常遠小於最壞情況，因為有啟發式

### 優化技巧
1. **對角移動**：允許斜向走（8方向）
   ```python
   directions = [
       (0, 1), (1, 0), (0, -1), (-1, 0),  # 四方向
       (1, 1), (1, -1), (-1, 1), (-1, -1)  # 對角
   ]
   # 對角成本為 sqrt(2) ≈ 1.414
   ```

2. **路徑平滑化**：A* 結果可能有鋸齒，可以後處理
   ```python
   def smooth_path(path):
       # 移除不必要的轉角
       # 使用射線檢測簡化路徑
   ```

3. **快取常用路徑**：如果玩家經常導航到同一地點

---

## 🎯 測試計劃

### 單元測試
- [ ] A* 找到最短路徑
- [ ] A* 正確處理無路徑情況
- [ ] Grid 正確標記碰撞區域
- [ ] NavigationManager 正確追蹤路徑

### 整合測試
- [ ] 玩家可以導航到所有 teleporter
- [ ] ESC 正確取消導航
- [ ] 速度切換正常工作
- [ ] 小地圖正確顯示所有元素

### 性能測試
- [ ] 大地圖（200×200）A* 執行時間 < 100ms
- [ ] 小地圖每幀渲染時間 < 5ms

---

## 📝 備註

### 已確認的設計決策
- ✅ 地標只使用 teleporter
- ✅ 小地圖範圍 15×15（可配置）
- ✅ 速度選項 [0.5, 1, 2, 4]
- ✅ 大地圖完全覆蓋（Overlay 或 Scene）
- ✅ 使用 A* 而非 BFS
- ✅ ESC 取消導航

### 待決定
- ❓ 大地圖用 Overlay 還是新 Scene？
  - **推薦 Overlay**：實作簡單，狀態管理容易
- ❓ 是否允許對角移動？
  - **推薦先四方向**：簡化實作
- ❓ 導航時是否顯示路徑？
  - **推薦顯示**：用戶體驗更好

---

*最後更新：2025-12-18*
*設計者討論記錄*
