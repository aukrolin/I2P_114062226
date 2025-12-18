import threading
import time
import uuid
import copy
from dataclasses import dataclass, field
from typing import Dict, Optional, Literal
from enum import Enum
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.utils.battle_calculator import calculate_damage, use_item_in_battle

BATTLE_TIMEOUT = 30.0  # 30 seconds timeout


class BattleStatus(Enum):
    WAITING_OPPONENT = "waiting_opponent"
    WAITING_ACTIONS = "waiting_actions"
    PROCESSING = "processing"
    FINISHED = "finished"
    TIMEOUT = "timeout"


@dataclass
class BattleAction:
    player_id: int
    action_type: str  # "attack", "use_item", "switch"
    data: dict
    timestamp: float


@dataclass
class Battle:
    battle_id: str
    player1_id: int
    player2_id: int
    player1_monsters: list[dict]
    player2_monsters: list[dict]
    player1_items: list[dict]
    player2_items: list[dict]
    player1_current_monster: int = 0  # Index of current monster
    player2_current_monster: int = 0
    player1_action: Optional[BattleAction] = None
    player2_action: Optional[BattleAction] = None
    status: BattleStatus = BattleStatus.WAITING_ACTIONS
    turn: int = 0
    last_update: float = field(default_factory=time.monotonic)
    last_result: Optional[dict] = None  # Store last turn result
    winner: Optional[int] = None


class BattleHandler:
    _lock: threading.Lock
    battles: Dict[str, Battle]
    player_battles: Dict[int, str]  # player_id -> battle_id
    
    def __init__(self):
        self._lock = threading.Lock()
        self.battles = {}
        self.player_battles = {}
    
    # ------------------------------------------------------------------
    # Battle Management
    # ------------------------------------------------------------------
    
    def create_battle(self, player1_id: int, player2_id: int, 
                     player1_data: dict, player2_data: dict) -> str:
        """Create a new battle between two players"""
        with self._lock:
            # Validate that both players have monsters
            p1_monsters = player1_data.get("monsters", [])
            p2_monsters = player2_data.get("monsters", [])
            
            if not p1_monsters or not p2_monsters:
                raise ValueError("Both players must have at least one monster")
            
            battle_id = str(uuid.uuid4())
            
            battle = Battle(
                battle_id=battle_id,
                player1_id=player1_id,
                player2_id=player2_id,
                player1_monsters=copy.deepcopy(p1_monsters),
                player2_monsters=copy.deepcopy(p2_monsters),
                player1_items=copy.deepcopy(player1_data.get("items", [])),
                player2_items=copy.deepcopy(player2_data.get("items", [])),
            )
            
            self.battles[battle_id] = battle
            self.player_battles[player1_id] = battle_id
            self.player_battles[player2_id] = battle_id
            
            return battle_id
    
    def get_battle(self, battle_id: str) -> Optional[Battle]:
        """Get battle by ID"""
        with self._lock:
            return self.battles.get(battle_id)
    
    def get_player_battle(self, player_id: int) -> Optional[Battle]:
        """Get battle for a player"""
        with self._lock:
            battle_id = self.player_battles.get(player_id)
            if battle_id:
                return self.battles.get(battle_id)
            return None
    
    def submit_action(self, battle_id: str, player_id: int, 
                     action_type: str, data: dict) -> bool:
        """Submit a player's action"""
        with self._lock:
            battle = self.battles.get(battle_id)
            if not battle:
                return False
            
            if battle.status != BattleStatus.WAITING_ACTIONS:
                return False
            
            action = BattleAction(
                player_id=player_id,
                action_type=action_type,
                data=data,
                timestamp=time.monotonic()
            )
            
            if player_id == battle.player1_id:
                battle.player1_action = action
            elif player_id == battle.player2_id:
                battle.player2_action = action
            else:
                return False
            
            # If both players submitted actions, process the turn
            if battle.player1_action and battle.player2_action:
                self._process_turn(battle)
            
            return True
    
    def _process_turn(self, battle: Battle):
        """Process a turn of battle"""
        import random
        
        battle.status = BattleStatus.PROCESSING
        battle.turn += 1
        
        # Safety checks
        if not battle.player1_monsters or not battle.player2_monsters:
            battle.status = BattleStatus.FINISHED
            battle.winner = battle.player2_id if battle.player1_monsters else battle.player1_id
            return
        
        if battle.player1_current_monster >= len(battle.player1_monsters):
            battle.player1_current_monster = 0
        if battle.player2_current_monster >= len(battle.player2_monsters):
            battle.player2_current_monster = 0
        
        # Get current monsters
        p1_monster = battle.player1_monsters[battle.player1_current_monster]
        p2_monster = battle.player2_monsters[battle.player2_current_monster]
        
        messages = []
        
        # Determine action order: switch actions go first, then speed-based
        actions = [(1, battle.player1_action, p1_monster, p2_monster),
                   (2, battle.player2_action, p2_monster, p1_monster)]
        
        # Sort: switch actions first, then random order for attacks/items
        def action_priority(action_tuple):
            player_num, action, _, _ = action_tuple
            if action.action_type == "switch":
                return 0  # Switch has highest priority
            else:
                return 1  # Attack/item second priority
        
        actions.sort(key=action_priority)
        
        # If both are same priority (both attack or both switch), randomize
        if action_priority(actions[0]) == action_priority(actions[1]):
            p1_first = random.choice([True, False])
            if not p1_first:
                actions.reverse()
        
        # Process actions in order
        for idx, (player_num, action, attacker, defender) in enumerate(actions):
            # Get actual monster references from battle (ensure we're modifying the real data)
            if player_num == 1:
                attacker = battle.player1_monsters[battle.player1_current_monster]
                defender = battle.player2_monsters[battle.player2_current_monster]
            else:
                attacker = battle.player2_monsters[battle.player2_current_monster]
                defender = battle.player1_monsters[battle.player1_current_monster]
            
            # Skip if attacker is dead
            if attacker["hp"] <= 0:
                messages.append(f"{attacker['name']} cannot attack (fainted)!")
                continue
            
            # Flag to skip defender death check (for switch actions)
            skip_damage_check = False
            
            # Process action
            if action.action_type == "attack":
                # Get move from action data
                move_index = action.data.get("move_index", 0)
                moves = attacker.get("moves", [])
                
                if moves and 0 <= move_index < len(moves):
                    move = moves[move_index]
                    damage, attack_messages = self._calculate_damage(attacker, defender, move)
                    messages.extend(attack_messages)
                    
                    old_hp = defender["hp"]
                    defender["hp"] = max(0, defender["hp"] - damage)
                    messages.append(f"{defender['name']}: {old_hp} -> {defender['hp']} HP")
                    print(f"[SERVER] {attacker['name']} used {move['name']}, dealt {damage} damage. {defender['name']}: {old_hp} -> {defender['hp']} HP")
                else:
                    # Fallback: basic attack
                    damage = max(1, attacker.get("level", 10))
                    old_hp = defender["hp"]
                    defender["hp"] = max(0, defender["hp"] - damage)
                    messages.append(f"{attacker['name']} attacked for {damage} damage!")
                    messages.append(f"{defender['name']}: {old_hp} -> {defender['hp']} HP")
                    print(f"[SERVER] {attacker['name']} basic attack: {damage} damage")
                    
            elif action.action_type == "use_item":
                item_name = action.data.get("item_name")
                self._use_item(battle, player_num, item_name, attacker, messages)
                # Items don't damage opponent, skip damage check
                skip_damage_check = True
                
            elif action.action_type == "switch":
                # Handle pokemon switching
                new_index = action.data.get("pokemon_index")
                monsters = battle.player1_monsters if player_num == 1 else battle.player2_monsters
                
                print(f"[SERVER] Player {player_num} switch action: new_index={new_index}, monsters count={len(monsters)}")
                
                if new_index is not None and 0 <= new_index < len(monsters):
                    new_monster = monsters[new_index]
                    print(f"[SERVER] Target monster: {new_monster['name']} HP={new_monster['hp']}")
                    
                    if new_monster["hp"] > 0:
                        # Update current monster index
                        old_index = battle.player1_current_monster if player_num == 1 else battle.player2_current_monster
                        if player_num == 1:
                            battle.player1_current_monster = new_index
                        else:
                            battle.player2_current_monster = new_index
                        messages.append(f"Player {player_num} switched to {new_monster['name']}!")
                        print(f"[SERVER] Player {player_num} switched from index {old_index} to {new_index} ({new_monster['name']})")
                        # Switch doesn't cause damage, skip damage check
                        skip_damage_check = True
                    else:
                        messages.append(f"Cannot switch to fainted {new_monster['name']}!")
                        print(f"[SERVER] Switch failed: target pokemon fainted")
                        skip_damage_check = True  # Also skip for failed switch
                else:
                    messages.append(f"Invalid pokemon switch!")
                    print(f"[SERVER] Invalid switch: index {new_index} out of range (0-{len(monsters)-1})")
                    skip_damage_check = True  # Also skip for invalid switch
            
            # Check if defender fainted (skip for switch/item actions)
            if not skip_damage_check and defender["hp"] <= 0:
                messages.append(f"{defender['name']} fainted!")
                
                # Check which player lost their monster
                if player_num == 1:  # P1 attacked, P2's monster fainted
                    battle.player2_current_monster = self._get_next_alive_monster(
                        battle.player2_monsters, battle.player2_current_monster)
                    if battle.player2_current_monster == -1:
                        battle.status = BattleStatus.FINISHED
                        battle.winner = battle.player1_id
                        messages.append(f"Player {battle.player1_id} wins!")
                        battle.last_result = {"messages": messages, "winner": battle.winner}
                        return
                    else:
                        # Update reference to new monster
                        new_monster = battle.player2_monsters[battle.player2_current_monster]
                        messages.append(f"Player 2 sent out {new_monster['name']}!")
                        print(f"[SERVER] P2 switched to {new_monster['name']}")
                else:  # P2 attacked, P1's monster fainted
                    battle.player1_current_monster = self._get_next_alive_monster(
                        battle.player1_monsters, battle.player1_current_monster)
                    if battle.player1_current_monster == -1:
                        battle.status = BattleStatus.FINISHED
                        battle.winner = battle.player2_id
                        messages.append(f"Player {battle.player2_id} wins!")
                        battle.last_result = {"messages": messages, "winner": battle.winner}
                        return
                    else:
                        # Update reference to new monster
                        new_monster = battle.player1_monsters[battle.player1_current_monster]
                        messages.append(f"Player 1 sent out {new_monster['name']}!")
                        print(f"[SERVER] P1 switched to {new_monster['name']}")
        
        # Reset actions and prepare for next turn
        battle.player1_action = None
        battle.player2_action = None
        battle.status = BattleStatus.WAITING_ACTIONS
        battle.last_update = time.monotonic()
        battle.last_result = {"messages": messages}
        
        print(f"[SERVER] Turn {battle.turn} complete. P1 current monster: index {battle.player1_current_monster}, P2 current monster: index {battle.player2_current_monster}")
        print(f"[SERVER] Turn result messages: {messages}")
    
    def _calculate_damage(self, attacker: dict, defender: dict, move: dict) -> tuple[int, list[str]]:
        """Calculate damage using battle_calculator with type effectiveness"""
        try:
            damage, messages = calculate_damage(attacker, defender, move)
            return damage, messages
        except Exception as e:
            print(f"[SERVER ERROR] calculate_damage failed: {e}")
            # Fallback to simple calculation
            base_damage = attacker.get("level", 10)
            damage = max(1, base_damage)
            return damage, [f"{attacker['name']} attacked {defender['name']}!"]
    
    def _use_item(self, battle: Battle, player_num: int, item_name: str, 
                  monster: dict, messages: list):
        """Use an item using battle_calculator"""
        items = battle.player1_items if player_num == 1 else battle.player2_items
        
        for item in items:
            if item["name"] == item_name and item["count"] > 0:
                try:
                    # Use battle_calculator's item system
                    item_messages = use_item_in_battle(monster, item)
                    messages.extend(item_messages)
                    
                    # Decrease item count
                    item["count"] -= 1
                    print(f"[SERVER] Used {item_name}, remaining: {item['count']}")
                except Exception as e:
                    print(f"[SERVER ERROR] use_item_in_battle failed: {e}")
                    # Fallback: simple heal
                    if item.get("effect") == "heal":
                        heal = item.get("value", 20)
                        old_hp = monster["hp"]
                        monster["hp"] = min(monster["hp"] + heal, monster["max_hp"])
                        actual_heal = monster["hp"] - old_hp
                        messages.append(f"Used {item_name}! {monster['name']} restored {actual_heal} HP!")
                        item["count"] -= 1
                
                break
    
    def _get_next_alive_monster(self, monsters: list[dict], current: int) -> int:
        """Get index of next alive monster, or -1 if none"""
        for i in range(len(monsters)):
            if i != current and monsters[i]["hp"] > 0:
                return i
        return -1
    
    def _create_result(self, battle: Battle, messages: list) -> dict:
        """Create result dictionary"""
        return {
            "turn": battle.turn,
            "status": battle.status.value,
            "player1_monster": battle.player1_monsters[battle.player1_current_monster] if battle.player1_current_monster >= 0 else None,
            "player2_monster": battle.player2_monsters[battle.player2_current_monster] if battle.player2_current_monster >= 0 else None,
            "player1_monster_index": battle.player1_current_monster,
            "player2_monster_index": battle.player2_current_monster,
            "messages": messages,
            "winner": battle.winner,
            "finished": battle.status == BattleStatus.FINISHED
        }
    
    def check_timeout(self, battle_id: str) -> bool:
        """Check if battle has timed out - MUST be called with lock already held"""
        battle = self.battles.get(battle_id)
        if not battle:
            return False
        
        if battle.status != BattleStatus.WAITING_ACTIONS:
            return False
        
        elapsed = time.monotonic() - battle.last_update
        if elapsed > BATTLE_TIMEOUT:
            # Determine who timed out
            if not battle.player1_action:
                battle.winner = battle.player2_id
                messages = [f"Player {battle.player1_id} timed out!", f"Player {battle.player2_id} wins!"]
            else:
                battle.winner = battle.player1_id
                messages = [f"Player {battle.player2_id} timed out!", f"Player {battle.player1_id} wins!"]
            
                battle.status = BattleStatus.TIMEOUT
                battle.result = self._create_result(battle, messages)
                return True
            
            return False
    
    def end_battle(self, battle_id: str) -> bool:
        """Mark battle as finished (don't delete immediately)"""
        with self._lock:
            battle = self.battles.get(battle_id)
            if not battle:
                return False
            
            # Mark as finished instead of deleting
            battle.status = BattleStatus.FINISHED
            print(f"[SERVER] Battle {battle_id} marked as FINISHED")
            
            return True
    
    def delete_battle(self, battle_id: str) -> bool:
        """Permanently delete a battle (call after both players acknowledged)"""
        with self._lock:
            battle = self.battles.get(battle_id)
            if not battle:
                return False
            
            # Remove from player battles
            if battle.player1_id in self.player_battles:
                del self.player_battles[battle.player1_id]
            if battle.player2_id in self.player_battles:
                del self.player_battles[battle.player2_id]
            
            # Remove battle
            del self.battles[battle_id]
            print(f"[SERVER] Battle {battle_id} permanently deleted")
            
            return True
    
    def get_battle_status(self, battle_id: str, player_id: int) -> Optional[dict]:
        """Get battle status for a player"""
        with self._lock:
            battle = self.battles.get(battle_id)
            if not battle:
                return None
            
            # Check timeout (only if not already finished)
            if battle.status != BattleStatus.FINISHED:
                self.check_timeout(battle_id)
            
            # Return complete battle state (client expects full data)
            return {
                "battle_id": battle_id,
                "player1_id": battle.player1_id,
                "player2_id": battle.player2_id,
                "player1_monsters": battle.player1_monsters,
                "player2_monsters": battle.player2_monsters,
                "player1_items": battle.player1_items,
                "player2_items": battle.player2_items,
                "turn_count": battle.turn,
                "status": battle.status.value,
                "winner": battle.winner,
                "last_turn_result": battle.last_result or {},
                "player1_current_monster": battle.player1_current_monster,
                "player2_current_monster": battle.player2_current_monster,
                "player1_action_submitted": battle.player1_action is not None,
                "player2_action_submitted": battle.player2_action is not None
            }
