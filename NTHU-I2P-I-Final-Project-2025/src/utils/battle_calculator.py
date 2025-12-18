"""
戰鬥計算模組

處理寶可夢戰鬥的傷害計算、物品使用等邏輯
"""

from logging import Logger
import random
from typing import Tuple
from src.utils.pokemon_data import get_type_effectiveness


def calculate_damage(attacker: dict, defender: dict, move: dict) -> tuple[int, list[str]]:
    """
    計算招式傷害
    
    使用寶可夢標準傷害公式：
    damage = ((2 × Level + 10) ÷ 250) × (Atk ÷ Def) × Power + 2) × STAB × Type × Random
    
    Args:
        attacker: 攻擊方寶可夢
        defender: 防禦方寶可夢
        move: 使用的招式
    
    Returns:
        (傷害值, 訊息列表)
    """
    messages = []
    
    # 取得招式資訊
    move_power = move.get("power", 40)
    move_type = move.get("type", "Normal")
    move_category = move.get("category", "physical")  # physical or special
    move_name = move.get("name", "Tackle")
    
    # 如果是狀態招式（power = 0），不造成傷害
    if move_power == 0:
        attacker_name = attacker.get("name", "Unknown")
        messages.append(f"{attacker_name} used {move_name}!")
        messages.append("But nothing happened...")
        return 0, messages
    
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
    # damage = ((2 * Level + 10) / 250) * (Atk / Def) * Power + 2
    base_damage = ((2 * level + 10) / 250) * (atk / defense) * move_power + 2
    
    # 屬性一致加成（STAB - Same Type Attack Bonus）
    attacker_types = attacker.get("element", ("Normal", None))
    stab = 1.5 if move_type in attacker_types else 1.0
    
    # 屬性相剋
    defender_types = defender.get("element", ("Normal", None))
    type_effectiveness = get_type_effectiveness(move_type, defender_types)
    
    # 隨機浮動 (0.85 ~ 1.0)
    random_factor = random.uniform(0.85, 1.0)
    
    # 最終傷害
    final_damage = int(base_damage * stab * type_effectiveness * random_factor)
    
    # 至少造成 1 點傷害（除非屬性無效）
    if type_effectiveness > 0:
        final_damage = max(1, final_damage)
    
    # 產生訊息
    attacker_name = attacker.get("name", "Unknown")
    defender_name = defender.get("name", "Unknown")
    
    messages.append(f"{attacker_name} used {move_name}!")
    
    if type_effectiveness == 0.0:
        messages.append(f"It doesn't affect {defender_name}...")
        final_damage = 0
    elif type_effectiveness >= 2.0:
        messages.append("It's super effective!")
    elif type_effectiveness <= 0.5 and type_effectiveness > 0:
        messages.append("It's not very effective...")
    
    return final_damage, messages


def use_item_in_battle(target_monster: dict, item: dict) -> tuple[bool, list[str]]:
    """
    在戰鬥中使用物品
    
    Args:
        target_monster: 目標寶可夢
        item: 使用的物品
    
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
            Logger.info(f"Failed to use item {item_name} in battle: HP full")
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
        # Logger.info(f"Cannot use item {item_name} in battle: effect {effect} not recognized")
        return False, messages


def reset_battle_boosts(monster: dict) -> None:
    """
    重置戰鬥增益效果（戰鬥結束時呼叫）
    
    Args:
        monster: 要重置的寶可夢
    """
    monster["attack_boost"] = 0
    monster["defense_boost"] = 0


def get_move_description(move: dict) -> str:
    """
    取得招式描述
    
    Args:
        move: 招式資料
    
    Returns:
        招式描述字串
    """
    name = move.get("name", "Unknown")
    power = move.get("power", 0)
    move_type = move.get("type", "Normal")
    category = move.get("category", "physical")
    
    if power == 0:
        return f"{name} ({move_type}/{category}) - Status move"
    else:
        return f"{name} ({move_type}/{category}) - Power: {power}"
