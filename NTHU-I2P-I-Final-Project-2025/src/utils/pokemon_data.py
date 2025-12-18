"""
寶可夢資料庫模組

包含所有寶可夢的基礎數值、屬性、招式等資訊
數值來源：saves/pokemon_def.py
"""

from typing import Tuple

# pokemon_def.py 數值順序：[HP, Attack, Defense, Sp.Atk, Sp.Def, Speed]

POKEMON_DATABASE = {
    "Pikachu": {
        "stats": [35, 55, 40, 50, 50, 90],
        "element": ("Electric", None),
        "sprite_path": "menu_sprites/menusprite1.png",
        "moves": [
            {"name": "Thunder Shock", "power": 40, "type": "Electric", "category": "special"},
            {"name": "Quick Attack", "power": 40, "type": "Normal", "category": "physical"},
        ],
        "can_evolve": False,
    },
    "Charizard": {
        "stats": [78, 84, 78, 109, 85, 100],
        "element": ("Fire", "Flying"),
        "sprite_path": "menu_sprites/menusprite2.png",
        "moves": [
            {"name": "Flamethrower", "power": 90, "type": "Fire", "category": "special"},
            {"name": "Wing Attack", "power": 60, "type": "Flying", "category": "physical"},
        ],
        "can_evolve": False,
    },
    "Blastoise": {
        "stats": [79, 83, 100, 85, 105, 78],
        "element": ("Water", None),
        "sprite_path": "menu_sprites/menusprite3.png",
        "moves": [
            {"name": "Water Gun", "power": 40, "type": "Water", "category": "special"},
            {"name": "Bite", "power": 60, "type": "Normal", "category": "physical"},
        ],
        "can_evolve": False,
    },
    "Venusaur": {
        "stats": [80, 82, 83, 100, 100, 80],
        "element": ("Grass", "Poison"),
        "sprite_path": "menu_sprites/menusprite4.png",
        "moves": [
            {"name": "Vine Whip", "power": 45, "type": "Grass", "category": "physical"},
            {"name": "Razor Leaf", "power": 55, "type": "Grass", "category": "physical"},
        ],
        "can_evolve": False,
    },
    "Gengar": {
        "stats": [60, 65, 60, 130, 75, 110],
        "element": ("Ghost", "Poison"),
        "sprite_path": "menu_sprites/menusprite5.png",
        "moves": [
            {"name": "Shadow Ball", "power": 80, "type": "Ghost", "category": "special"},
            {"name": "Lick", "power": 30, "type": "Ghost", "category": "physical"},
        ],
        "can_evolve": False,
    },
    "Dragonite": {
        "stats": [91, 134, 95, 100, 100, 80],
        "element": ("Dragon", "Flying"),
        "sprite_path": "menu_sprites/menusprite6.png",
        "moves": [
            {"name": "Dragon Claw", "power": 80, "type": "Dragon", "category": "physical"},
            {"name": "Wing Attack", "power": 60, "type": "Flying", "category": "physical"},
        ],
        "can_evolve": False,
    },
    "Squirtle": {
        "stats": [44, 48, 65, 50, 64, 43],
        "element": ("Water", None),
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
        "element": ("Bug", "Flying"),
        "sprite_path": "menu_sprites/menusprite8.png",
        "moves": [
            {"name": "Gust", "power": 40, "type": "Flying", "category": "special"},
            {"name": "Tackle", "power": 40, "type": "Normal", "category": "physical"},
        ],
        "can_evolve": False,
    },
    "Eevee": {
        "stats": [55, 55, 50, 45, 65, 55],
        "element": ("Normal", None),
        "sprite_path": "menu_sprites/menusprite9.png",
        "moves": [
            {"name": "Tackle", "power": 40, "type": "Normal", "category": "physical"},
            {"name": "Quick Attack", "power": 40, "type": "Normal", "category": "physical"},
        ],
        "can_evolve": False,  # 可以之後擴充多種進化
    },
    "Jigglypuff": {
        "stats": [115, 45, 20, 45, 25, 20],
        "element": ("Normal", "Fairy"),
        "sprite_path": "menu_sprites/menusprite10.png",
        "moves": [
            {"name": "Pound", "power": 40, "type": "Normal", "category": "physical"},
            {"name": "Sing", "power": 0, "type": "Normal", "category": "status"},
        ],
        "can_evolve": False,
    },
    "Pidgeotto": {
        "stats": [63, 60, 55, 50, 50, 71],
        "element": ("Normal", "Flying"),
        "sprite_path": "menu_sprites/menusprite11.png",
        "moves": [
            {"name": "Wing Attack", "power": 60, "type": "Flying", "category": "physical"},
            {"name": "Quick Attack", "power": 40, "type": "Normal", "category": "physical"},
        ],
        "can_evolve": False,
    },
    "Rattata": {
        "stats": [30, 56, 35, 25, 35, 72],
        "element": ("Normal", None),
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
        "Bug": 2.0,
        "Steel": 2.0,
    },
    "Water": {
        "Fire": 2.0,
        "Grass": 0.5,
        "Water": 0.5,
        "Ground": 2.0,
        "Rock": 2.0,
        "Dragon": 0.5,
    },
    "Grass": {
        "Water": 2.0,
        "Fire": 0.5,
        "Grass": 0.5,
        "Ground": 2.0,
        "Rock": 2.0,
        "Poison": 0.5,
        "Flying": 0.5,
        "Bug": 0.5,
        "Dragon": 0.5,
    },
    "Electric": {
        "Water": 2.0,
        "Flying": 2.0,
        "Electric": 0.5,
        "Grass": 0.5,
        "Ground": 0.0,  # 無效
        "Dragon": 0.5,
    },
    "Normal": {
        "Rock": 0.5,
        "Ghost": 0.0,  # 無效
        "Steel": 0.5,
    },
    "Flying": {
        "Grass": 2.0,
        "Fighting": 2.0,
        "Bug": 2.0,
        "Electric": 0.5,
        "Rock": 0.5,
        "Steel": 0.5,
    },
    "Ghost": {
        "Ghost": 2.0,
        "Psychic": 2.0,
        "Normal": 0.0,  # 無效
        "Dark": 0.5,
    },
    "Dragon": {
        "Dragon": 2.0,
        "Steel": 0.5,
        "Fairy": 0.0,  # 無效
    },
    "Poison": {
        "Grass": 2.0,
        "Fairy": 2.0,
        "Poison": 0.5,
        "Ground": 0.5,
        "Rock": 0.5,
        "Ghost": 0.5,
        "Steel": 0.0,  # 無效
    },
    "Bug": {
        "Grass": 2.0,
        "Psychic": 2.0,
        "Dark": 2.0,
        "Fire": 0.5,
        "Fighting": 0.5,
        "Poison": 0.5,
        "Flying": 0.5,
        "Ghost": 0.5,
        "Steel": 0.5,
        "Fairy": 0.5,
    },
    "Fairy": {
        "Fighting": 2.0,
        "Dragon": 2.0,
        "Dark": 2.0,
        "Fire": 0.5,
        "Poison": 0.5,
        "Steel": 0.5,
    },
}


def get_type_effectiveness(attacker_type: str, defender_types: Tuple[str, str | None]) -> float:
    """
    取得屬性相剋倍率（支援雙屬性防禦方）
    
    Args:
        attacker_type: 攻擊方招式屬性
        defender_types: 防禦方的屬性 (type1, type2 or None)
    
    Returns:
        最終倍率（如果有兩個屬性，倍率會相乘）
    """
    if attacker_type not in TYPE_EFFECTIVENESS:
        return 1.0
    
    multiplier = 1.0
    
    # 檢查第一屬性
    type1 = defender_types[0]
    multiplier *= TYPE_EFFECTIVENESS[attacker_type].get(type1, 1.0)
    
    # 檢查第二屬性（如果有）
    type2 = defender_types[1]
    if type2:
        multiplier *= TYPE_EFFECTIVENESS[attacker_type].get(type2, 1.0)
    
    return multiplier


def create_monster_from_template(name: str, level: int) -> dict:
    """
    根據寶可夢名稱和等級建立完整的寶可夢資料
    
    Args:
        name: 寶可夢名稱
        level: 等級
    
    Returns:
        完整的寶可夢字典
    """
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
        "moves": [move.copy() for move in template["moves"]],
        "can_evolve": template.get("can_evolve", False),
        "evolution_item": template.get("evolution_item"),
        "evolution_target": template.get("evolution_target"),
    }


def get_pokemon_info(name: str) -> dict | None:
    """取得寶可夢的基礎資訊"""
    return POKEMON_DATABASE.get(name)
