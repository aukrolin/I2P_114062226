"""
進化管理模組

處理寶可夢進化相關邏輯
"""

from src.utils.pokemon_data import POKEMON_DATABASE, create_monster_from_template


def can_evolve_with_item(monster: dict, item: dict) -> bool:
    """
    檢查寶可夢是否能用此道具進化
    
    Args:
        monster: 寶可夢資料
        item: 物品資料
    
    Returns:
        是否可以進化
    """
    if not monster.get("can_evolve", False):
        return False
    
    if item.get("effect") != "evolution":
        return False
    
    # 方法 1: 檢查寶可夢是否需要這個進化石
    required_item = monster.get("evolution_item")
    item_name = item.get("name")
    
    if required_item and item_name == required_item:
        return True
    
    # 方法 2: 檢查道具的 target 列表是否包含這個寶可夢
    targets = item.get("target", [])
    if targets and monster.get("name") in targets:
        return True
    
    return False


def evolve_monster(monster: dict) -> tuple[dict, list[str]]:
    """
    執行寶可夢進化
    
    Args:
        monster: 要進化的寶可夢
    
    Returns:
        (進化後的寶可夢, 訊息列表)
    """
    messages = []
    old_name = monster["name"]
    evolution_target = monster.get("evolution_target")
    
    if not evolution_target:
        messages.append(f"{old_name} cannot evolve!")
        return monster, messages
    
    if evolution_target not in POKEMON_DATABASE:
        messages.append(f"Evolution target {evolution_target} not found!")
        return monster, messages
    
    # 保留原有的 HP 比例和等級
    current_hp = monster["hp"]
    current_max_hp = monster["max_hp"]
    current_level = monster["level"]
    
    # 計算 HP 比例
    hp_ratio = current_hp / current_max_hp if current_max_hp > 0 else 1.0
    
    # 建立進化後的寶可夢
    evolved_monster = create_monster_from_template(evolution_target, current_level)
    
    # 保持當前 HP 比例
    evolved_monster["hp"] = int(evolved_monster["max_hp"] * hp_ratio)
    
    # 確保 HP 不為 0（除非原本就是 0）
    if current_hp > 0 and evolved_monster["hp"] == 0:
        evolved_monster["hp"] = 1
    
    messages.append(f"What? {old_name} is evolving!")
    messages.append(f"Congratulations! {old_name} evolved into {evolution_target}!")
    
    return evolved_monster, messages


def get_evolution_requirements(monster: dict) -> str | None:
    """
    取得寶可夢的進化需求描述
    
    Args:
        monster: 寶可夢資料
    
    Returns:
        進化需求描述，若不可進化則返回 None
    """
    if not monster.get("can_evolve", False):
        return None
    
    evolution_item = monster.get("evolution_item")
    evolution_target = monster.get("evolution_target")
    
    if evolution_item and evolution_target:
        return f"Use {evolution_item} to evolve into {evolution_target}"
    
    return "Evolution requirements unknown"


def check_all_evolutions(monsters: list[dict]) -> list[tuple[int, str]]:
    """
    檢查所有寶可夢中哪些可以進化
    
    Args:
        monsters: 寶可夢列表
    
    Returns:
        可進化寶可夢的索引和需求描述列表
    """
    evolvable = []
    
    for idx, monster in enumerate(monsters):
        if monster.get("can_evolve", False):
            requirement = get_evolution_requirements(monster)
            if requirement:
                evolvable.append((idx, requirement))
    
    return evolvable
