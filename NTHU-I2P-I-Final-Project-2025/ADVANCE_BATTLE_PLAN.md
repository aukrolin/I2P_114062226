# Advance Battle 實作計劃

## 📋 總覽

本文件詳細記錄 Checkpoint 3 - Advance Battle 的實作步驟。

### 目標功能 (4 points)
1. **屬性系統** (2 points) - 寶可夢屬性與相剋機制
2. **戰鬥物品** (1 point) - 三種藥水效果
3. **進化系統** (1 point) - 使用道具進化

---

## 🎯 第一階段：數據結構更新

### 1.1 更新 Monster TypedDict (`src/utils/definition.py`)

**現有結構：**
```python
class Monster(TypedDict):
    name: str
    hp: int
    max_hp: int
    level: int
    sprite_path: str
```

**新增欄位：**
```python
class Monster(TypedDict):
    name: str
    hp: int
    max_hp: int
    level: int
    sprite_path: str
    # 新增欄位
    element: Tuple[str, str|None]           # 屬性類型 (Fire, Water, Grass, Electric, Normal, etc.) # maxium 2 types
    base_hp: int          # 基礎 HP (來自 pokemon_def.py)
    attack: int           # 攻擊力 (物理攻擊)
    defense: int          # 防禦力 (物理防禦)
    sp_attack: int        # 特殊攻擊
    sp_defense: int       # 特殊防禦
    speed: int            # 速度
    attack_boost: int     # 攻擊力增益 (藥水效果，預設 0)
    defense_boost: int    # 防禦力增益 (藥水效果，預設 0)
    moves: list[dict]     # 招式列表 (未來擴充)
    can_evolve: bool      # 是否可進化
    evolution_item: str | None  # 進化所需道具 (例如 "Water Stone")
    evolution_target: str | None  # 進化後的寶可夢名稱
```

### 1.2 更新 Item TypedDict (`src/utils/definition.py`)

**新增欄位：**
```python
class Item(TypedDict):
    name: str
    count: int
    sprite_path: str
    # 新增欄位
    price: int            # 物品價格 (選用，商店物品需要)
    effect: str           # 物品效果類型 (heal, attack_boost, defense_boost, evolution)
    value: int            # 效果數值 (恢復量/增益量)
    target: list[str] | None    # 進化石目標 (例如 "Squirtle")
```

### 1.3 建立寶可夢資料庫 (`src/utils/pokemon_data.py` - 新檔案)

根據 `saves/pokemon_def.py` 的數值建立完整資料庫：

```python
# pokemon_def.py 數值順序：[HP, Attack, Defense, Sp.Atk, Sp.Def, Speed]

POKEMON_DATABASE = {
    "Pikachu": {
        "stats": [35, 55, 40, 50, 50, 90],
        "element": "Electric",
        "sprite_path": "menu_sprites/menusprite1.png",
        "moves": [
            {"name": "Thunder Shock", "power": 40, "type": "Electric", "category": "special"},
            {"name": "Quick Attack", "power": 40, "type": "Normal", "category": "physical"},
        ],
        "can_evolve": False,
    },
    "Charizard": {
        "stats": [78, 84, 78, 109, 85, 100],
        "element": "Fire",
        "sprite_path": "menu_sprites/menusprite2.png",
        "moves": [
            {"name": "Flamethrower", "power": 90, "type": "Fire", "category": "special"},
            {"name": "Wing Attack", "power": 60, "type": "Flying", "category": "physical"},
        ],
        "can_evolve": False,
    },
    "Blastoise": {
        "stats": [79, 83, 100, 85, 105, 78],
        "element": "Water",
        "sprite_path": "menu_sprites/menusprite3.png",
        "moves": [
            {"name": "Water Gun", "power": 40, "type": "Water", "category": "special"},
            {"name": "Bite", "power": 60, "type": "Normal", "category": "physical"},
        ],
        "can_evolve": False,
    },
    "Venusaur": {
        "stats": [80, 82, 83, 100, 100, 80],
        "element": "Grass",
        "sprite_path": "menu_sprites/menusprite4.png",
        "moves": [
            {"name": "Vine Whip", "power": 45, "type": "Grass", "category": "physical"},
            {"name": "Razor Leaf", "power": 55, "type": "Grass", "category": "physical"},
        ],
        "can_evolve": False,
    },
    "Gengar": {
        "stats": [60, 65, 60, 130, 75, 110],
        "element": "Ghost",
        "sprite_path": "menu_sprites/menusprite5.png",
        "moves": [
            {"name": "Shadow Ball", "power": 80, "type": "Ghost", "category": "special"},
            {"name": "Lick", "power": 30, "type": "Ghost", "category": "physical"},
        ],
        "can_evolve": False,
    },
    "Dragonite": {
        "stats": [91, 134, 95, 100, 100, 80],
        "element": "Dragon",
        "sprite_path": "menu_sprites/menusprite6.png",
        "moves": [
            {"name": "Dragon Claw", "power": 80, "type": "Dragon", "category": "physical"},
            {"name": "Wing Attack", "power": 60, "type": "Flying", "category": "physical"},
        ],
        "can_evolve": False,
    },
    "Squirtle": {
        "stats": [44, 48, 65, 50, 64, 43],
        "element": "Water",
        "sprite_path": "menu_sprites/menusprite7.png",
        "moves": [
            {"name": "Water Gun", "power": 40, "type": "Water", "category": "special"},
            {"name": "Tackle", "power": 40, "type": "Normal", "category": "physical"},
        ],
        "can_evolve": True,
        "evolution_item": "Water Stone",
        "evolution_target": "Blastoise",
    },
    "Butterfree": {
        "stats": [60, 45, 50, 90, 80, 70],
        "element": "Flying",
        "sprite_path": "menu_sprites/menusprite8.png",
        "moves": [
            {"name": "Gust", "power": 40, "type": "Flying", "category": "special"},
            {"name": "Tackle", "power": 40, "type": "Normal", "category": "physical"},
        ],
        "can_evolve": False,
    },
    "Eevee": {
        "stats": [55, 55, 50, 45, 65, 55],
        "element": "Normal",
        "sprite_path": "menu_sprites/menusprite9.png",
        "moves": [
            {"name": "Tackle", "power": 40, "type": "Normal", "category": "physical"},
            {"name": "Quick Attack", "power": 40, "type": "Normal", "category": "physical"},
        ],
        "can_evolve": False,  # 可以之後擴充多種進化
    },
    "Jigglypuff": {
        "stats": [115, 45, 20, 45, 25, 20],
        "element": "Normal",
        "sprite_path": "menu_sprites/menusprite10.png",
        "moves": [
            {"name": "Pound", "power": 40, "type": "Normal", "category": "physical"},
            {"name": "Sing", "power": 0, "type": "Normal", "category": "status"},
        ],
        "can_evolve": False,
    },
    "Pidgeotto": {
        "stats": [63, 60, 55, 50, 50, 71],
        "element": "Flying",
        "sprite_path": "menu_sprites/menusprite11.png",
        "moves": [
            {"name": "Wing Attack", "power": 60, "type": "Flying", "category": "physical"},
            {"name": "Quick Attack", "power": 40, "type": "Normal", "category": "physical"},
        ],
        "can_evolve": False,
    },
    "Rattata": {
        "stats": [30, 56, 35, 25, 35, 72],
        "element": "Normal",
        "sprite_path": "menu_sprites/menusprite12.png",
        "moves": [
            {"name": "Tackle", "power": 40, "type": "Normal", "category": "physical"},
            {"name": "Quick Attack", "power": 40, "type": "Normal", "category": "physical"},
        ],
        "can_evolve": False,
    },
}

# 屬性相剋表
TYPE_EFFECTIVENESS = {
    "Fire": {
        "Grass": 2.0,
        "Water": 0.5,
        "Fire": 0.5,
        "Ice": 2.0,
    },
    "Water": {
        "Fire": 2.0,
        "Grass": 0.5,
        "Water": 0.5,
        "Ground": 2.0,
        "Rock": 2.0,
    },
    "Grass": {
        "Water": 2.0,
        "Fire": 0.5,
        "Grass": 0.5,
        "Ground": 2.0,
        "Rock": 2.0,
    },
    "Electric": {
        "Water": 2.0,
        "Flying": 2.0,
        "Electric": 0.5,
        "Grass": 0.5,
        "Ground": 0.0,  # 無效
    },
    "Normal": {},  # 普通系無相剋
    "Flying": {
        "Grass": 2.0,
        "Fighting": 2.0,
        "Electric": 0.5,
        "Rock": 0.5,
    },
    "Ghost": {
        "Ghost": 2.0,
        "Normal": 0.0,  # 無效
    },
    "Dragon": {
        "Dragon": 2.0,
    },
}


def get_type_effectiveness(attacker_type: str, defender_type: str) -> float:
    """取得屬性相剋倍率"""
    if attacker_type not in TYPE_EFFECTIVENESS:
        return 1.0
    return TYPE_EFFECTIVENESS[attacker_type].get(defender_type, 1.0)


def create_monster_from_template(name: str, level: int) -> dict:
    """根據寶可夢名稱和等級建立完整的寶可夢資料"""
    if name not in POKEMON_DATABASE:
        raise ValueError(f"Unknown pokemon: {name}")
    
    template = POKEMON_DATABASE[name]
    stats = template["stats"]
    
    # 計算實際數值（根據等級調整）
    # 簡化公式：實際值 = 基礎值 + (基礎值 * level * 0.1)
    hp = int(stats[0] + (stats[0] * level * 0.1))
    
    return {
        "name": name,
        "hp": hp,
        "max_hp": hp,
        "level": level,
        "sprite_path": template["sprite_path"],
        "element": template["element"],
        "base_hp": stats[0],
        "attack": stats[1],
        "defense": stats[2],
        "sp_attack": stats[3],
        "sp_defense": stats[4],
        "speed": stats[5],
        "attack_boost": 0,
        "defense_boost": 0,
        "moves": template["moves"].copy(),
        "can_evolve": template.get("can_evolve", False),
        "evolution_item": template.get("evolution_item"),
        "evolution_target": template.get("evolution_target"),
    }
```

---

## 🔥 第二階段：屬性系統實作

### 2.1 建立戰鬥計算工具 (`src/utils/battle_calculator.py` - 新檔案)

```python
import random
from src.utils.pokemon_data import get_type_effectiveness


def calculate_damage(attacker: dict, defender: dict, move: dict) -> tuple[int, list[str]]:
    """
    計算招式傷害
    
    公式：damage = ((2 * Level + 10) / 250) * (Atk/Def) * Power + 2) * Multipliers
    
    Returns:
        (傷害值, 訊息列表)
    """
    messages = []
    
    # 取得招式資訊
    move_power = move.get("power", 40)
    move_type = move.get("type", "Normal")
    move_category = move.get("category", "physical")  # physical or special
    
    # 取得攻擊方與防禦方數值
    level = attacker.get("level", 1)
    
    if move_category == "physical":
        atk = attacker.get("attack", 50) + attacker.get("attack_boost", 0)
        defense = defender.get("defense", 50) + defender.get("defense_boost", 0)
    else:  # special
        atk = attacker.get("sp_attack", 50) + attacker.get("attack_boost", 0)
        defense = defender.get("sp_defense", 50) + defender.get("defense_boost", 0)
    
    # 避免除以零
    if defense <= 0:
        defense = 1
    
    # 基礎傷害計算
    base_damage = ((2 * level + 10) / 250) * (atk / defense) * move_power + 2
    
    # 屬性一致加成（STAB - Same Type Attack Bonus）
    stab = 1.5 if move_type == attacker.get("element", "Normal") else 1.0
    
    # 屬性相剋
    type_effectiveness = get_type_effectiveness(move_type, defender.get("element", "Normal"))
    
    # 隨機浮動 (0.85 ~ 1.0)
    random_factor = random.uniform(0.85, 1.0)
    
    # 最終傷害
    final_damage = int(base_damage * stab * type_effectiveness * random_factor)
    
    # 至少造成 1 點傷害
    final_damage = max(1, final_damage)
    
    # 產生訊息
    attacker_name = attacker.get("name", "Unknown")
    defender_name = defender.get("name", "Unknown")
    move_name = move.get("name", "Tackle")
    
    messages.append(f"{attacker_name} used {move_name}!")
    
    if type_effectiveness > 1.0:
        messages.append("It's super effective!")
    elif type_effectiveness < 1.0 and type_effectiveness > 0:
        messages.append("It's not very effective...")
    elif type_effectiveness == 0.0:
        messages.append("It doesn't affect the opponent...")
        final_damage = 0
    
    return final_damage, messages


def use_item_in_battle(target_monster: dict, item: dict) -> tuple[bool, list[str]]:
    """
    在戰鬥中使用物品
    
    Returns:
        (是否成功, 訊息列表)
    """
    messages = []
    item_name = item.get("name", "Unknown Item")
    effect = item.get("effect", "")
    value = item.get("value", 0)
    
    if effect == "heal":
        # 恢復 HP
        old_hp = target_monster["hp"]
        target_monster["hp"] = min(target_monster["max_hp"], target_monster["hp"] + value)
        actual_heal = target_monster["hp"] - old_hp
        
        if actual_heal > 0:
            messages.append(f"Used {item_name}!")
            messages.append(f"{target_monster['name']} recovered {actual_heal} HP!")
            return True, messages
        else:
            messages.append(f"{target_monster['name']}'s HP is already full!")
            return False, messages
    
    elif effect == "attack_boost":
        # 增加攻擊力
        target_monster["attack_boost"] = target_monster.get("attack_boost", 0) + value
        messages.append(f"Used {item_name}!")
        messages.append(f"{target_monster['name']}'s Attack rose!")
        return True, messages
    
    elif effect == "defense_boost":
        # 增加防禦力
        target_monster["defense_boost"] = target_monster.get("defense_boost", 0) + value
        messages.append(f"Used {item_name}!")
        messages.append(f"{target_monster['name']}'s Defense rose!")
        return True, messages
    
    else:
        messages.append(f"Cannot use {item_name} in battle!")
        return False, messages
```

### 2.2 修改戰鬥場景 (`src/scenes/battle_scene.py`)

需要修改的地方：
1. 離線戰鬥的傷害計算（約 Line 600-630）
2. 選擇招式的 UI（目前是直接攻擊）
3. 顯示屬性相剋訊息

---

## 💊 第三階段：戰鬥物品實作

### 3.1 更新商店物品列表 (`saves/start.json` 和 `saves/game1.json`)

在 Shop.tmx 的商店 NPC 背包中添加三種藥水：

```json
{
  "name": "clerk",
  "bag": {
    "selling_items": [
      {
        "name": "Heal Potion",
        "count": 99,
        "sprite_path": "ingame_ui/heal_potion.png",
        "price": 200,
        "effect": "heal",
        "value": 50
      },
      {
        "name": "Strength Potion",
        "count": 99,
        "sprite_path": "ingame_ui/strength_potion.png",
        "price": 300,
        "effect": "attack_boost",
        "value": 20
      },
      {
        "name": "Defense Potion",
        "count": 99,
        "sprite_path": "ingame_ui/defense_potion.png",
        "price": 300,
        "effect": "defense_boost",
        "value": 15
      },
      {
        "name": "Water Stone",
        "count": 5,
        "sprite_path": "ingame_ui/water_stone.png",
        "price": 2100,
        "effect": "evolution",
        "target": "Squirtle"
      }
    ]
  }
}
```

### 3.2 修改背包 Overlay 顯示物品效果

在 `src/overlay/bag_overlay.py` 中：
- 顯示物品的效果描述
- 在戰鬥中只能使用特定物品

### 3.3 修改戰鬥場景的物品使用邏輯

在 `src/scenes/battle_scene.py` 中：
- BAG 選項選擇物品後，呼叫 `use_item_in_battle()`
- 顯示物品效果訊息
- 扣除物品數量

---

## 🌟 第四階段：進化系統實作

### 4.1 建立進化管理器 (`src/utils/evolution_manager.py` - 新檔案)

```python
from src.utils.pokemon_data import POKEMON_DATABASE, create_monster_from_template


def can_evolve_with_item(monster: dict, item: dict) -> bool:
    """檢查寶可夢是否能用此道具進化"""
    if not monster.get("can_evolve", False):
        return False
    
    if item.get("effect") != "evolution":
        return False
    
    required_item = monster.get("evolution_item")
    item_name = item.get("name")
    
    # 檢查是否是對的進化石
    if required_item and item_name == required_item:
        return True
    
    # 或檢查道具的 target 是否符合
    if item.get("target") == monster.get("name"):
        return True
    
    return False


def evolve_monster(monster: dict) -> tuple[dict, list[str]]:
    """
    執行寶可夢進化
    
    Returns:
        (進化後的寶可夢, 訊息列表)
    """
    messages = []
    old_name = monster["name"]
    evolution_target = monster.get("evolution_target")
    
    if not evolution_target:
        messages.append(f"{old_name} cannot evolve!")
        return monster, messages
    
    # 保留原有的 HP 和等級
    current_hp = monster["hp"]
    current_level = monster["level"]
    
    # 建立進化後的寶可夢
    evolved_monster = create_monster_from_template(evolution_target, current_level)
    
    # 保持當前 HP 比例
    hp_ratio = current_hp / monster["max_hp"]
    evolved_monster["hp"] = int(evolved_monster["max_hp"] * hp_ratio)
    
    messages.append(f"What? {old_name} is evolving!")
    messages.append(f"Congratulations! {old_name} evolved into {evolution_target}!")
    
    return evolved_monster, messages
```

### 4.2 在背包 Overlay 添加進化功能

在 `src/overlay/bag_overlay.py` 中：
- 選擇寶可夢
- 選擇進化石
- 確認進化
- 播放進化動畫（可選）

### 4.3 修改 GameManager 處理進化

在遊戲場景中使用進化石時：
- 彈出寶可夢選擇介面
- 選擇要進化的寶可夢
- 執行進化並更新數據

---

## 🎮 第五階段：招式選擇系統（未來擴充）

### 5.1 建立招式選擇 UI (`src/interface/components/move_selector.py` - 新檔案)

```python
# 戰鬥中顯示 4 個招式按鈕
# 玩家選擇要使用的招式
# 顯示招式的 PP、威力、屬性等資訊
```

### 5.2 修改戰鬥場景整合招式選擇

- BATTLE 選項進入招式選擇畫面
- 選擇招式後執行攻擊
- 顯示招式效果

---

## 📝 實作順序建議

### 階段一：資料結構 (30 分鐘)
1. ✅ 創建 `src/utils/pokemon_data.py`
2. ✅ 更新 `src/utils/definition.py` 的 TypedDict
3. ✅ 創建 `src/utils/battle_calculator.py`
4. ✅ 創建 `src/utils/evolution_manager.py`

### 階段二：遊戲數據更新 (20 分鐘)
5. ✅ 更新所有 JSON 存檔中的寶可夢數據（添加新欄位）
6. ✅ 更新商店物品列表（添加藥水和進化石）

### 階段三：戰鬥系統整合 (40 分鐘)
7. ✅ 修改 `battle_scene.py` 使用新的傷害計算
8. ✅ 實作物品使用功能
9. ✅ 顯示屬性相剋訊息
10. ✅ 測試離線戰鬥

### 階段四：進化系統 (30 分鐘)
11. ✅ 修改 `bag_overlay.py` 添加進化功能
12. ✅ 實作進化邏輯
13. ✅ 測試進化流程

### 階段五：線上戰鬥相容性 (20 分鐘)
14. ✅ 確保新系統與線上戰鬥相容
15. ✅ 更新伺服器戰鬥處理邏輯（如果需要）

### 階段六：測試與調整 (30 分鐘)
16. ✅ 完整測試所有功能
17. ✅ 數值平衡調整
18. ✅ Bug 修復

---

## 🔧 技術細節筆記

### 傷害計算公式
```
damage = ((2 × Level + 10) ÷ 250) × (Atk ÷ Def) × Power + 2) × STAB × Type × Random

其中：
- STAB = 1.5 (招式屬性與寶可夢屬性相同)
- Type = 0.0 / 0.5 / 1.0 / 2.0 (屬性相剋倍率)
- Random = 0.85 ~ 1.0 (隨機浮動)
```

### 藥水效果持續時間
- **Heal Potion**: 立即恢復 HP
- **Strength Potion**: 整場戰鬥有效（戰鬥結束後重置）
- **Defense Potion**: 整場戰鬥有效（戰鬥結束後重置）

### 進化機制
- 使用進化石即可進化（不需要等級限制）
- 進化後保持當前 HP 比例
- 進化後等級不變，但數值提升
- 進化石消耗一次

---

## ✅ 檢查清單

- [ ] Monster TypedDict 更新完成
- [ ] Item TypedDict 更新完成
- [ ] pokemon_data.py 創建完成
- [ ] battle_calculator.py 創建完成
- [ ] evolution_manager.py 創建完成
- [ ] JSON 存檔數據更新完成
- [ ] 商店物品添加完成
- [ ] 戰鬥傷害計算整合完成
- [ ] 物品使用功能完成
- [ ] 進化系統完成
- [ ] 屬性相剋訊息顯示完成
- [ ] 離線戰鬥測試通過
- [ ] 線上戰鬥相容性測試通過
- [ ] 最終驗收測試通過

---

## 🎯 預期成果

完成後應該能夠：
1. ✅ 戰鬥中看到屬性相剋效果（"Super effective!" 等訊息）
2. ✅ 在商店購買並使用三種藥水
3. ✅ 使用水之石將 Squirtle 進化成 Blastoise
4. ✅ 所有功能在離線和線上戰鬥中都正常運作

---

**準備好開始實作了嗎？讓我們從第一階段開始！** 🚀
