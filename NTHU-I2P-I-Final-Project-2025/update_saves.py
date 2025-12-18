"""
更新遊戲存檔數據的腳本
添加新的寶可夢屬性和戰鬥物品
"""

import json
import sys
sys.path.insert(0, '/home/aukro/Main/main/hackthon/NTHU-I2P-I-Final-Project-2025')

from src.utils.pokemon_data import POKEMON_DATABASE


def update_monster(monster_data: dict) -> dict:
    """
    更新單個寶可夢的數據，添加新欄位
    """
    name = monster_data.get("name")
    level = monster_data.get("level", 1)
    
    if name not in POKEMON_DATABASE:
        print(f"Warning: {name} not found in database, skipping")
        return monster_data
    
    template = POKEMON_DATABASE[name]
    stats = template["stats"]
    
    # 計算實際 HP（如果需要）
    base_max_hp = int(stats[0] + (stats[0] * level * 0.1))
    
    # 如果 max_hp 不合理，更新它
    current_max_hp = monster_data.get("max_hp", base_max_hp)
    if current_max_hp < 10:  # 不合理的值
        current_max_hp = base_max_hp
    
    # 保持當前 HP 比例
    current_hp = monster_data.get("hp", current_max_hp)
    if current_hp > current_max_hp:
        current_hp = current_max_hp
    
    # 更新寶可夢數據
    updated = {
        "name": name,
        "hp": current_hp,
        "max_hp": current_max_hp,
        "level": level,
        "sprite_path": monster_data.get("sprite_path", template["sprite_path"]),
        # 新增欄位
        "element": template["element"],
        "base_hp": stats[0],
        "attack": stats[1],
        "defense": stats[2],
        "sp_attack": stats[3],
        "sp_defense": stats[4],
        "speed": stats[5],
        "attack_boost": 0,
        "defense_boost": 0,
        "moves": [move.copy() for move in template["moves"]],
        "can_evolve": template.get("can_evolve", False),
    }
    
    # 可選欄位（只有可進化的才添加）
    if template.get("can_evolve", False):
        updated["evolution_item"] = template.get("evolution_item")
        updated["evolution_target"] = template.get("evolution_target")
    
    return updated


def update_save_file(input_path: str, output_path: str):
    """
    更新存檔文件
    """
    print(f"\n=== Processing {input_path} ===")
    
    # 讀取原始檔案
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 更新玩家背包中的寶可夢
    if "bag" in data and "monsters" in data["bag"]:
        print(f"Updating player monsters ({len(data['bag']['monsters'])} monsters)...")
        updated_monsters = []
        for monster in data["bag"]["monsters"]:
            print(f"  - {monster['name']} (Level {monster['level']})")
            updated_monsters.append(update_monster(monster))
        data["bag"]["monsters"] = updated_monsters
    
    # 更新地圖中的敵人訓練師寶可夢
    if "map" in data:
        for map_data in data["map"]:
            if "enemy_trainers" in map_data:
                for trainer in map_data["enemy_trainers"]:
                    if "bag" in trainer and "monsters" in trainer["bag"]:
                        print(f"Updating trainer '{trainer['name']}' monsters ({len(trainer['bag']['monsters'])} monsters)...")
                        updated_monsters = []
                        for monster in trainer["bag"]["monsters"]:
                            print(f"  - {monster['name']} (Level {monster['level']})")
                            updated_monsters.append(update_monster(monster))
                        trainer["bag"]["monsters"] = updated_monsters
                    
                    # 更新商店物品（如果是 clerk）
                    if trainer.get("name") == "clerk" and "bag" in trainer:
                        print(f"Updating shop items for clerk...")
                        trainer["bag"]["selling_items"] = [
                            {
                                "name": "Potion",
                                "sprite_path": "ingame_ui/potion.png",
                                "price": 300,
                                "effect": "heal",
                                "value": 20
                            },
                            {
                                "name": "Pokeball",
                                "sprite_path": "ingame_ui/ball.png",
                                "price": 200
                            },
                            {
                                "name": "Heal Potion",
                                "sprite_path": "ingame_ui/potion.png",
                                "price": 200,
                                "effect": "heal",
                                "value": 50
                            },
                            {
                                "name": "Strength Potion",
                                "sprite_path": "ingame_ui/potion.png",
                                "price": 300,
                                "effect": "attack_boost",
                                "value": 20
                            },
                            {
                                "name": "Defense Potion",
                                "sprite_path": "ingame_ui/potion.png",
                                "price": 300,
                                "effect": "defense_boost",
                                "value": 15
                            },
                            {
                                "name": "Water Stone",
                                "sprite_path": "ingame_ui/ball.png",
                                "price": 2100,
                                "effect": "evolution",
                                "target": ["Squirtle"]
                            }
                        ]
                        print(f"  Added 6 items to shop")
    
    # 寫入更新後的檔案
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Successfully updated {output_path}")


if __name__ == "__main__":
    # 更新 start.json
    update_save_file(
        "/home/aukro/Main/main/hackthon/NTHU-I2P-I-Final-Project-2025/saves/start.json",
        "/home/aukro/Main/main/hackthon/NTHU-I2P-I-Final-Project-2025/saves/start.json"
    )
    
    # 更新 game1.json
    update_save_file(
        "/home/aukro/Main/main/hackthon/NTHU-I2P-I-Final-Project-2025/saves/game1.json",
        "/home/aukro/Main/main/hackthon/NTHU-I2P-I-Final-Project-2025/saves/game1.json"
    )
    
    print("\n=== All save files updated successfully! ===")
