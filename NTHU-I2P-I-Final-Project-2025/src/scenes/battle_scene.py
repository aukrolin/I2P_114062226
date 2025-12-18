import pygame as pg
import math
import random

from src.utils import GameSettings, Logger
from src.sprites import BackgroundSprite
from src.scenes.scene import Scene
from src.interface.components import Button
from src.overlay.battleDialog_overlay import BattleDialogOverlay
from src.overlay.battleoverlay import BattleOverlay
from src.core.services import scene_manager, sound_manager, input_manager, set_game_manager, get_game_manager, get_online_manager
from src.utils.battle_calculator import calculate_damage, use_item_in_battle
from typing import override
from enum import Enum


class DialogState(Enum):
    DIALOG = 0
    OPTIONS = 1
    BATTLE = 2
class BattleState(Enum):
    NPC = 'enemy'
    WILD = "bush_pokemon"
    ONLINE_BATTLE = "online_battle"
    NOBATTLE = "nobattle"
class OptionsState(Enum):
    BATTLE = 0
    BAG = 1
    POKEMON = 2
    RUNAWAY = 3
# class BattleManager: 


'''


'''



class BattleScene(Scene):
    # Background Image
    background: BackgroundSprite
    # Buttons
    play_button: Button
    
    def __init__(self) -> None:
        super().__init__()
        self.background = BackgroundSprite("backgrounds/background2.png")
        self.state = DialogState.DIALOG  # 初始狀態設為對話 
        self.kind = None
        self.DialogOverlay : BattleDialogOverlay = BattleDialogOverlay(lambda: set_game_manager("saves/game1.json"))
        self.BattleOverlay : BattleOverlay = BattleOverlay()
        self.options_state = OptionsState.BATTLE
        self.components  = [self.background, self.BattleOverlay, self.DialogOverlay]
        self.online_manager = get_online_manager()
        
        # Move/Item/Pokemon selection
        self.selected_move_index = 0  # 當前選擇的招式索引 (0 或 1)
        self.selected_item_index = 0  # 當前選擇的物品索引
        self.selected_pokemon_index = 0  # 當前選擇的寶可夢索引
        self.just_switched_pokemon = False  # 標記是否剛切換寶可夢（避免重複觸發）
        self.just_used_item = False  # 標記是否剛使用道具（需要執行敵人回合）
        
        # Online battle state
        self.battle_id = None
        self.waiting_for_opponent = False
        self.last_turn_count = 0  # Start from 0, server turn_count starts at 0
        self.action_submitted = False
        self.battle_ended = False
        self.end_battle_timer = 0.0
        self.END_BATTLE_DELAY = 2.0  # Wait 2 seconds before exiting
        self.should_delete_battle = False
        self.submitting_action = False  # Prevent duplicate submissions
            
        # Dialog pagination
        self.dialog_messages = []  # Store all messages
        self.dialog_page_index = 0  # Current page index
        self.waiting_for_next_page = False  # Flag to wait for space key

    @override
    def enter(self) -> None:
        sound_manager.play_bgm("RBY 101 Opening (Part 1).ogg")
        self.state = DialogState.DIALOG  # 初始狀態設為對話 
        self.doing = 0
        self.DialogOverlay.dialog_textA = ""
        self.DialogOverlay.dialog_text = ""
        self.win = False
        self.lost = False
        
        # 檢查我方寶可夢是否全部 HP = 0
        if "online_battle" not in self.info:
            monsters = get_game_manager().bag.get_monsters()
            if all(m['hp'] <= 0 for m in monsters):
                self.DialogOverlay.dialog_text = "All your Pokemon have fainted!"
                print("[BATTLE_END] LOSE INFO: All player Pokemon HP = 0 (enter stage)")
                self.lost = True
                self.kind = BattleState.NOBATTLE
                scene_manager.change_scene("game")
                return
        
        print(f"[DEBUG] self.info.keys(): {self.info.keys()}")
        # 設定 BattleOverlay 的戰鬥資訊
        print(f"[DEBUG] Setting BattleOverlay with info: {self.info}")
        self.BattleOverlay.set_battle_info(self.info)
        
        if "bush_pokemon" in self.info:
            self.kind = BattleState.WILD
            self.DialogOverlay.dialog_text = f"Wild {self.info['bush_pokemon']['name']} appeared!"
        elif "enemy_trainers" in self.info:
            Emonsters = self.info['bag'].get_monsters()
            Emonster = Emonsters[0]
            if Emonster['hp'] <= 0:
                # 訓練家的寶可夢已經全部倒下，直接返回遊戲場景
                print("[DEBUG] Enemy trainer has no available Pokemon, skipping battle")
                scene_manager.change_scene("game")
                return
            
            self.kind = BattleState.NPC
            self.DialogOverlay.dialog_text = f"{self.info['name']} wants to battle!"
        elif "online_battle" in self.info:
            def get_opponent_monster():
                if self.online_manager.player_id == battle_status.get('player1_id') : return battle_status.get('player2_monsters', [])
                else : return battle_status.get('player1_monsters', [])
                




            self.kind = BattleState.ONLINE_BATTLE
            opponent_id = self.info['online_battle']['opponent_id']
            self.game_manager = get_game_manager()
            
            # Check if joining existing battle or creating new one
            if self.info['online_battle'].get('is_joiner'):
                # P2: Join existing battle
                self.battle_id = self.info['online_battle']['battle_id'] #to indentify which battle to join
                self.waiting_for_opponent = False
                self.action_submitted = False
                self.last_turn_count = 0  # Start from 0, matches server initial turn_count
                self.state = DialogState.DIALOG  # Start with dialog like offline battles
                
                self.DialogOverlay.dialog_text = f"Joined online battle!"
                Logger.info(f"Joined battle: {self.battle_id}")
                
                # Fetch initial battle status to get opponent's monsters
                battle_status = self.online_manager.get_battle_status(self.battle_id) #get battle status from server
                print(f"[DEBUG P2] Initial battle_status: {battle_status}")
                if battle_status:
                    # Set up BattleOverlay with online battle data
                    opponent_monsters = get_opponent_monster()
                    
                    print(f"[DEBUG P2] Opponent monsters: {opponent_monsters}")
                    
                    # Create fake info for BattleOverlay
                    from src.data.bag import Bag
                    op_bag = Bag()
                    op_bag.monsters = opponent_monsters
                    # Remove bush_pokemon to avoid confusion
                    if 'bush_pokemon' in self.info:
                        del self.info['bush_pokemon']
                    
                    self.info['bag'] = op_bag
                    self.info['name'] = f"Player {opponent_id}"
                    print(f"[DEBUG P2] Setting BattleOverlay with opponent data: {opponent_monsters[0]['name'] if opponent_monsters else 'None'}")
                    self.BattleOverlay.set_battle_info(self.info)
            else:
                # P1: Create new battle
                my_monsters = self.game_manager.bag.get_monsters()
                my_items = self.game_manager.bag.get_items()
                
                # Create battle on server (send my data, server fetches opponent data)
                result = self.online_manager.create_battle(opponent_id, my_monsters, my_items)
                
                if result and result.get('success') and 'battle_id' in result:
                    self.battle_id = result['battle_id']
                    self.waiting_for_opponent = False
                    self.action_submitted = False
                    self.last_turn_count = 0  # Start from 0, matches server initial turn_count
                    self.state = DialogState.DIALOG  # Start with dialog
                    self.DialogOverlay.dialog_text = f"Online battle started!"
                    print(f"[DEBUG P1] Battle created: {self.battle_id}")
                    print(f"[DEBUG P1] Create result: {result}")
                    
                    # Get opponent's monsters from server response
                    opponent_monsters = result.get('player2_monsters', [])
                    print(f"[DEBUG P1] Opponent monsters from server: {opponent_monsters}")
                    
                    # Create fake info for BattleOverlay
                    from src.data.bag import Bag
                    fake_bag = Bag()
                    fake_bag.monsters = opponent_monsters
                    
                    # Remove bush_pokemon to avoid confusion
                    if 'bush_pokemon' in self.info:
                        del self.info['bush_pokemon']
                    
                    self.info['bag'] = fake_bag
                    self.info['name'] = f"Player {opponent_id}"
                    print(f"[DEBUG P1] Setting BattleOverlay with opponent data: {opponent_monsters[0]['name'] if opponent_monsters else 'None'}")
                    self.BattleOverlay.set_battle_info(self.info)
                    self.DialogOverlay.dialog_text = f"Online battle started!"
                    print(f"Battle created: {self.battle_id}")
                else:
                    print("Failed to create battle")
                    scene_manager.change_scene("game")
                    return

        print(f"Entered Battle Scene, Battle with: {self.info}, state={self.kind}")  # Debug info
        pass

    @override
    def exit(self) -> None:
        pass

    def update_content(self, dt: float) -> None:
            
        # Immediate exit for offline battles only
        if (self.win or self.lost) and self.kind != BattleState.ONLINE_BATTLE:
            if self.win:
                self.handle_win()
            else:
                self.handle_lost()
            return
        
        # For online battles, battle_ended flag is set but we wait for dialog pagination to finish
        # The actual exit happens in dialog pagination logic
        self.DialogOverlay.state = self.state
        self.game_manager = get_game_manager() 
        Monsters = self.game_manager.bag.get_monsters()
        items = self.game_manager.bag.get_items()
        Monster = None
        Monster = Monsters[0]

        if self.kind  == BattleState.WILD:
            Emonster = self.info['bush_pokemon']
        elif self.kind == BattleState.NPC:
            Emonsters = self.info['bag'].get_monsters()
            Emonster = Emonsters[0]
        elif self.kind == BattleState.ONLINE_BATTLE:
            # Online battle doesn't use Emonster variable
            Emonster = None
        elif self.kind == BattleState.NOBATTLE:
            # NOBATTLE 已在 enter() 處理，這裡不應該被執行到
            # 如果執行到這裡表示邏輯錯誤，直接返回場景
            print("[WARNING] NOBATTLE state reached in update_content, this should not happen")
            scene_manager.change_scene("game")
            return  
        # print(Emonster)
        print(self.state, self.options_state)
        if self.state == DialogState.DIALOG:
            if input_manager.key_pressed(pg.K_SPACE):
                # 進入 OPTIONS 前檢查當前寶可夢 HP
                if Monster['hp'] <= 0:
                    # 檢查是否有其他可用寶可夢
                    has_available = any(m['hp'] > 0 for m in Monsters[1:])
                    if has_available:
                        # 強制進入寶可夢選擇
                        self.state = DialogState.BATTLE
                        self.options_state = OptionsState.POKEMON
                        self.selected_pokemon_index = 0
                        self._update_pokemon_selection_display(force_switch=True)
                        return
                    else:
                        # 沒有可用寶可夢，戰敗
                        self.DialogOverlay.dialog_text = ["All your Pokemon have fainted!"]
                        print("[BATTLE_END] LOSE INFO: No available Pokemon in DIALOG state")
                        self.lost = True
                        self.handle_lost()
                        return
                
                self.state = DialogState.OPTIONS
                self.options_state = OptionsState.BATTLE
                self.DialogOverlay.dialog_text = None
                return
        if self.state == DialogState.OPTIONS:
            # For online battles, block input if waiting for results
            if self.kind == BattleState.ONLINE_BATTLE:
                if self.waiting_for_opponent or self.action_submitted:
                    # Show waiting message and block all input
                    if self.waiting_for_opponent:
                        self.DialogOverlay.dialog_text = ["Waiting for opponent..."]
                    return
            
            if self.options_state == OptionsState.BATTLE:
                if input_manager.key_pressed(pg.K_RIGHT) or input_manager.key_pressed(pg.K_d):
                    self.options_state = OptionsState.BAG
                elif input_manager.key_pressed(pg.K_DOWN) or input_manager.key_pressed(pg.K_s):
                    self.options_state = OptionsState.POKEMON
                elif input_manager.key_pressed(pg.K_k) or input_manager.key_pressed(pg.K_SPACE):
                    # 進入招式選擇狀態
                    self.state = DialogState.BATTLE
                    self.selected_move_index = 0  # 重置選擇
                    if self.kind != BattleState.ONLINE_BATTLE:
                        self.info['cannot_run'] = True
                    # 顯示招式選擇介面
                    self._update_move_selection_display()
                    return
            elif self.options_state == OptionsState.BAG:
                if input_manager.key_pressed(pg.K_LEFT) or input_manager.key_pressed(pg.K_a):
                    self.options_state = OptionsState.BATTLE
                elif input_manager.key_pressed(pg.K_DOWN) or input_manager.key_pressed(pg.K_s):
                    self.options_state = OptionsState.RUNAWAY
                elif input_manager.key_pressed(pg.K_k) or input_manager.key_pressed(pg.K_SPACE):
                    # 進入物品選擇狀態
                    self.state = DialogState.BATTLE
                    self.selected_item_index = 0  # 重置選擇
                    self._update_item_selection_display()
                    return
            elif self.options_state == OptionsState.POKEMON:
                if input_manager.key_pressed(pg.K_UP) or input_manager.key_pressed(pg.K_w):
                    self.options_state = OptionsState.BATTLE
                elif input_manager.key_pressed(pg.K_RIGHT) or input_manager.key_pressed(pg.K_d):
                    self.options_state = OptionsState.RUNAWAY
                elif input_manager.key_pressed(pg.K_k) or input_manager.key_pressed(pg.K_SPACE):
                    # 進入寶可夢選擇狀態
                    self.state = DialogState.BATTLE
                    self.selected_pokemon_index = 0  # 重置選擇
                    self._update_pokemon_selection_display()
                    return
            elif self.options_state == OptionsState.RUNAWAY:
                if input_manager.key_pressed(pg.K_UP) or input_manager.key_pressed(pg.K_w):
                    self.options_state = OptionsState.BAG
                elif input_manager.key_pressed(pg.K_LEFT) or input_manager.key_pressed(pg.K_a):
                    self.options_state = OptionsState.POKEMON
                elif input_manager.key_pressed(pg.K_k) or input_manager.key_pressed(pg.K_SPACE):
                    if self.kind == BattleState.ONLINE_BATTLE:
                        self.DialogOverlay.dialog_textA = "You cannot run away from online battles!"
                        return
                    elif self.kind == BattleState.WILD or (self.kind == BattleState.NPC and not self.info.get("cannot_run", False)):
                        scene_manager.change_scene("game")
            self.DialogOverlay.dialog_text = [
                f'->{i}' if i.replace(" ", "").lower() == self.options_state.name.lower() else i
                for i in ['Battle', 'Bag', 'Pokemon', 'Run Away']
            ]
            return
        if self.state == DialogState.BATTLE:
            # 處理招式/物品/寶可夢選擇（離線和線上戰鬥都需要）
            # Online battle: 選擇後返回OPTIONS，然後自動提交
            # Offline battle: 選擇後直接執行
            is_online = self.kind == BattleState.ONLINE_BATTLE
            
            if True:  # 允許所有戰鬥進入選擇邏輯
                if self.options_state == OptionsState.BATTLE and not self.just_used_item and not self.just_switched_pokemon:
                    # 招式選擇模式
                    monsters = self.game_manager.bag.get_monsters()
                    Monster = monsters[0]
                    moves = Monster.get('moves', [])
                    if not moves:
                        moves = [{"name": "Tackle", "power": 40, "type": "Normal", "category": "physical"}]
                    
                    max_index = len(moves[:2])  # 招式數量 + Back 選項
                    
                    if input_manager.key_pressed(pg.K_DOWN) or input_manager.key_pressed(pg.K_s):
                        self.selected_move_index = (self.selected_move_index + 1) % (max_index + 1)
                        self._update_move_selection_display()
                        return
                    elif input_manager.key_pressed(pg.K_UP) or input_manager.key_pressed(pg.K_w):
                        self.selected_move_index = (self.selected_move_index - 1) % (max_index + 1)
                        self._update_move_selection_display()
                        return
                    elif input_manager.key_pressed(pg.K_ESCAPE):
                        # 返回 OPTIONS
                        self.state = DialogState.OPTIONS
                        self.DialogOverlay.dialog_text = None
                        return
                    elif input_manager.key_pressed(pg.K_k) or input_manager.key_pressed(pg.K_SPACE):
                        # 檢查是否選擇 Back
                        if self.selected_move_index == max_index:
                            self.state = DialogState.OPTIONS
                            self.DialogOverlay.dialog_text = None
                            return
                        
                        # Online battle: 選擇完成，繼續進入BATTLE狀態觸發自動提交
                        # (不改變state，讓下面的online battle邏輯處理)
                        if is_online:
                            # selected_move_index已設定，繼續執行下面的online battle提交邏輯
                            pass
                        
                        # Offline battle: 確認選擇招式，繼續戰鬥
                        # 繼續往下執行戰鬥邏輯
                    else:
                        return  # 等待玩家選擇
                
                elif self.options_state == OptionsState.BAG:
                    # 物品選擇模式
                    items = self.game_manager.bag.get_items()
                    usable_items = [item for item in items if item['count'] > 0 and ('Pokeball' in item['name'] or 'Potion' in item['name'])]
                    
                    num_usable = len(usable_items)
                    # Back 選項的索引是 num_usable
                    max_total_index = num_usable  # 包含 Back 選項
                    
                    if input_manager.key_pressed(pg.K_DOWN) or input_manager.key_pressed(pg.K_s):
                        # 在所有物品 + Back 間循環
                        self.selected_item_index = (self.selected_item_index + 1) % (max_total_index + 1)
                        self._update_item_selection_display()
                        return
                    elif input_manager.key_pressed(pg.K_UP) or input_manager.key_pressed(pg.K_w):
                        self.selected_item_index = (self.selected_item_index - 1) % (max_total_index + 1)
                        self._update_item_selection_display()
                        return
                    elif input_manager.key_pressed(pg.K_ESCAPE):
                        # 返回 OPTIONS
                        self.state = DialogState.OPTIONS
                        self.DialogOverlay.dialog_text = None
                        return
                    elif input_manager.key_pressed(pg.K_k) or input_manager.key_pressed(pg.K_SPACE):
                        # 檢查是否選擇 Back（Back 的索引是 num_usable）
                        if not usable_items or self.selected_item_index == num_usable:
                            self.state = DialogState.OPTIONS
                            self.DialogOverlay.dialog_text = None
                            return
                        
                        # 確認使用物品（確保索引在範圍內）
                        actual_item_index = min(self.selected_item_index, num_usable - 1)
                        selected_item = usable_items[actual_item_index]
                        
                        # Online battle: 選擇完成，跳過offline邏輯，繼續執行下面的online battle提交邏輯
                        if not is_online:
                            # Offline battle only: 處理 Pokeball（僅野生戰鬥）
                            if 'Pokeball' in selected_item['name'] and self.kind == BattleState.WILD:
                                Emonsters = self.info.get('bag', None)
                                Emonster = None

                                if Emonsters:
                                    Ems = Emonsters.get_monsters()
                                    Emonster = Ems[0] if Ems else None
                                if not Emonster and "bush_pokemon" in self.info:
                                    Emonster = self.info['bush_pokemon']
                                
                                if Emonster:
                                    selected_item['count'] -= 1
                                    ballr = 1
                                    status = 1
                                    a = (3 * Emonster['max_hp'] - 2 * Emonster['hp']) / (3 * Emonster['max_hp']) * Emonster['catch_rate'] * ballr * status
                                    G = 1048560 / (int(math.sqrt(math.sqrt(16711680 / a))))
                                    nums = [random.randint(0, 65535) for _ in range(4)]
                                    shake = sum(1 for num in nums if num < G)

                                    self.just_used_item = True
                                    self.doing = 0  # 設為 0，讓下一幀檢查 just_used_item
                                    self.options_state = OptionsState.BATTLE  # 改變 state 避免重複進入
                                    Logger.info(f"Used Pokeball on {Emonster['name']} in battle, and got {shake} shakes")
                                    self.DialogOverlay.dialog_textA = f"You used a Pokeball on {Emonster['name']} and got {shake} shakes! {selected_item['count']} left."


                                    if shake >= 4:
                                        self.DialogOverlay.dialog_textA += f" Gotcha! {Emonster['name']} was caught!"
                                        self.game_manager.bag.add_monster(Emonster)
                                        print(f"[BATTLE_END] WIN INFO: Caught {Emonster['name']} with Pokeball")
                                        self.win = True
                                    return
                            
                            # Offline battle: 處理藥水
                            else:
                                monsters = self.game_manager.bag.get_monsters()
                                if monsters:
                                    success, messages = use_item_in_battle(monsters[0], selected_item)
                                    if success:
                                        selected_item['count'] -= 1
                                        self.DialogOverlay.dialog_text = messages
                                        # 設置標記，表示剛使用道具，準備執行敵人回合
                                        self.just_used_item = True
                                        self.doing = 0  # 設為 0，讓下一幀檢查 just_used_item
                                        self.options_state = OptionsState.BATTLE  # 改變 state 避免重複進入
                                        Logger.info(f"Used item {selected_item['name']} in battle")
                                        return  # 等待下一幀處理
                                    else:
                                        Logger.info(f"Failed to use item {selected_item['name']} in battle")
                                        self.DialogOverlay.dialog_text = messages
                                        self.state = DialogState.OPTIONS
                                        return
                    else:
                        return  # 等待玩家選擇
                
                elif self.options_state == OptionsState.POKEMON:
                    # 寶可夢選擇模式
                    monsters = self.game_manager.bag.get_monsters()
                    switchable_monsters = [(i, m) for i, m in enumerate(monsters[1:], start=1) if m['hp'] > 0]
                    
                    # 檢查是否是強制切換（當前寶可夢 HP = 0）
                    force_switch = monsters[0]['hp'] <= 0
                    
                    if not switchable_monsters:
                        if force_switch:
                            # 強制切換但沒有可用寶可夢 = 戰敗
                            self.DialogOverlay.dialog_text = ["All your Pokemon have fainted!"]
                            print("[BATTLE_END] LOSE INFO: No switchable Pokemon during forced switch")
                            self.lost = True
                            return
                        else:
                            self.DialogOverlay.dialog_textA = "No Pokemon to switch!"
                            self.state = DialogState.OPTIONS
                            return
                    
                    num_switchable = len(switchable_monsters)
                    # 計算最大索引（不含 Back 選項）
                    max_pokemon_index = num_switchable - 1
                    # 如果有 Back 選項，最大索引+1
                    max_total_index = max_pokemon_index + (1 if not force_switch else 0)
                    
                    if input_manager.key_pressed(pg.K_DOWN) or input_manager.key_pressed(pg.K_s):
                        if force_switch:
                            # 強制切換時沒有 Back 選項，只在寶可夢間循環
                            self.selected_pokemon_index = (self.selected_pokemon_index + 1) % num_switchable
                        else:
                            # 有 Back 選項，包含在循環中
                            self.selected_pokemon_index = (self.selected_pokemon_index + 1) % (max_total_index + 1)
                        self._update_pokemon_selection_display(force_switch)
                        return
                    elif input_manager.key_pressed(pg.K_UP) or input_manager.key_pressed(pg.K_w):
                        if force_switch:
                            # 強制切換時沒有 Back 選項
                            self.selected_pokemon_index = (self.selected_pokemon_index - 1) % num_switchable
                        else:
                            # 有 Back 選項
                            self.selected_pokemon_index = (self.selected_pokemon_index - 1) % (max_total_index + 1)
                        self._update_pokemon_selection_display(force_switch)
                        return
                    elif input_manager.key_pressed(pg.K_ESCAPE):
                        # 強制切換模式不能取消
                        if force_switch:
                            return
                        # 返回 OPTIONS
                        self.state = DialogState.OPTIONS
                        self.options_state = None
                        self.DialogOverlay.dialog_text = None
                        return
                    elif input_manager.key_pressed(pg.K_k) or input_manager.key_pressed(pg.K_SPACE):
                        # 檢查是否選擇 Back（Back 選項在最後）
                        if not force_switch and self.selected_pokemon_index == num_switchable:
                            self.state = DialogState.OPTIONS
                            self.DialogOverlay.dialog_text = None
                            return
                        
                        # 確認切換寶可夢（確保索引在範圍內）
                        actual_pokemon_index = min(self.selected_pokemon_index, num_switchable - 1)
                        real_idx, selected_pokemon = switchable_monsters[actual_pokemon_index]
                        
                        # Online battle: 選擇完成，保存索引並跳過offline邏輯
                        if is_online:
                            # 保存選擇的pokemon索引（注意：使用real_idx作為實際索引）
                            self.selected_pokemon_index = real_idx
                            # 跳過offline切換邏輯，繼續執行下面的online battle提交邏輯
                        else:
                            # Offline battle: 交換寶可夢位置
                            if self._switch_player_pokemon(real_idx):
                                print(1)
                                if force_switch:
                                    # 強制切換後返回選項（不消耗回合）
                                    print(2)
                                    self.state = DialogState.OPTIONS
                                    
                                    self.doing = 0
                                    self.DialogOverlay.dialog_text = None
                                    self.just_switched_pokemon = False
                                    return
                                else:
                                    print(3 )
                                    # 主動切換消耗回合，需要執行敵人攻擊
                                    # 設置標記，表示剛切換完，準備執行敵人回合
                                    self.just_switched_pokemon = True
                                    self.doing = 0  # 設為 0，讓下面的邏輯觸發敵人回合
                                    # 改變 options_state，避免下一幀又進入 POKEMON 選擇邏輯
                                    # self.state = DialogState.
                                    self.options_state = OptionsState.BATTLE
                                    # MUST return 這裡，讓下一幀檢查 just_switched_pokemon
                                    return
                            else:
                                return
                    else:
                        return  # 等待玩家選擇
            
            # Handle dialog pagination first (for online battles)
            if self.kind == BattleState.ONLINE_BATTLE and self.waiting_for_next_page:
                if input_manager.key_pressed(pg.K_SPACE):
                    self.dialog_page_index += 1
                    if self.dialog_page_index < len(self.dialog_messages):
                        # Show next message
                        self.DialogOverlay.dialog_text = [self.dialog_messages[self.dialog_page_index]]
                    else:
                        # All messages shown
                        self.waiting_for_next_page = False
                        self.dialog_page_index = 0
                        # If battle ended, exit now
                        if self.battle_ended:
                            if self.win:
                                self.handle_win()
                            else:
                                self.handle_lost()
                            return
                        # If battle continues, return to OPTIONS
                        else:
                            self.state = DialogState.OPTIONS
                            self.options_state = OptionsState.BATTLE
                            self.submitting_action = False
                            self.DialogOverlay.dialog_text = None
                return  # Don't process other logic while waiting for pagination
            
            # Handle online battle first (has its own logic)
            if self.kind == BattleState.ONLINE_BATTLE:
                # Online battle: Stage 1 & 3 (submit action + poll results)
                if not self.action_submitted and not self.submitting_action:
                    # Stage 1: Auto-submit action based on previous options_state choice
                    self.submitting_action = True  # Lock to prevent duplicate submission
                    
                    # Determine action type from options_state
                    action_type = "attack"  # default
                    action_data = {}
                    action_description = "attack"
                    
                    if self.options_state == OptionsState.BATTLE:
                        # Use selected move index
                        action_type = "attack"
                        move_index = self.selected_move_index
                        if Monster and Monster.get("moves"):
                            moves = Monster["moves"]
                            if 0 <= move_index < len(moves):
                                move_name = moves[move_index]["name"]
                                action_data = {"move_index": move_index}
                                action_description = f"use {move_name}"
                            else:
                                action_data = {"move_index": 0}
                                action_description = "attack"
                        else:
                            action_data = {"move_index": 0}
                            action_description = "attack"
                            
                    elif self.options_state == OptionsState.BAG:
                        # Use selected item index
                        usable_items = [item for item in items if item['count'] > 0]
                        if usable_items and 0 <= self.selected_item_index < len(usable_items):
                            selected_item = usable_items[self.selected_item_index]
                            action_type = "use_item"
                            action_data = {"item_name": selected_item['name']}
                            action_description = f"use {selected_item['name']}"
                        else:
                            # Fallback to first item or attack
                            if usable_items:
                                action_type = "use_item"
                                action_data = {"item_name": usable_items[0]['name']}
                                action_description = f"use {usable_items[0]['name']}"
                            else:
                                action_type = "attack"
                                action_data = {"move_index": 0}
                                action_description = "attack"
                                
                    elif self.options_state == OptionsState.POKEMON:
                        # Pokemon switching
                        action_type = "switch"
                        action_data = {"pokemon_index": self.selected_pokemon_index}
                        print(f"[DEBUG] Online battle switch: selected_pokemon_index={self.selected_pokemon_index}, monsters count={len(monsters) if monsters else 0}")
                        if monsters and 0 <= self.selected_pokemon_index < len(monsters):
                            pokemon_name = monsters[self.selected_pokemon_index]['name']
                            action_description = f"switch to {pokemon_name}"
                            print(f"[DEBUG] Switching to {pokemon_name} at index {self.selected_pokemon_index}")
                        else:
                            action_description = "switch pokemon"
                            print(f"[DEBUG] Invalid pokemon index: {self.selected_pokemon_index}")
                    
                    # Submit action automatically upon entering BATTLE state
                    print(f"[BATTLE] Submitting {action_description}...")
                    self.DialogOverlay.dialog_text = [f"Submitting {action_description}..."]
                    result = self.online_manager.submit_battle_action(
                        battle_id=self.battle_id,
                        action_type=action_type,
                        data=action_data
                    )
                    if result:
                        self.action_submitted = True
                        self.waiting_for_opponent = True
                        self.DialogOverlay.dialog_text = ["Waiting for opponent..."]
                        print("[BATTLE] Action submitted successfully")
                    else:
                        self.DialogOverlay.dialog_text = ["Failed to submit action"]
                        print("[BATTLE] Failed to submit action")
                        self.submitting_action = False  # Unlock on failure
                        # Go back to options on failure
                        self.state = DialogState.OPTIONS
                elif self.submitting_action and not self.action_submitted:
                    # Still submitting, show waiting message
                    # Debuging branch - should be very brief , maybe use if the internet is slow
                    self.DialogOverlay.dialog_text = ["Submitting action..."]
                else:
                    # Stage 3: Poll battle status
                    battle_status = self.online_manager.get_battle_status(self.battle_id)
                    if not battle_status: #ERROR HANDLING
                        # If we can't get status, battle was deleted - exit gracefully
                        # Use pagination system for exit message
                        self.dialog_messages = ["Battle ended by opponent"]
                        self.dialog_page_index = 0
                        self.waiting_for_next_page = True
                        self.DialogOverlay.dialog_text = [self.dialog_messages[0]]
                        self.battle_ended = True
                        print("[BATTLE_END] LOSE INFO: Online battle - battle_status is None (opponent left)")
                        self.lost = True
                        return
                    
                    # Check if battle is already marked as FINISHED
                    if battle_status.get('status') == 'finished':
                        print("[BATTLE] Battle already finished, checking results...")
                        # Process final state - UPDATE POKEMON STATUS FIRST
                        my_id = self.online_manager.player_id
                        player1_id = battle_status.get('player1_id')
                        player2_id = battle_status.get('player2_id')
                        
                        # Update final pokemon status before showing result
                        if player1_id and player2_id:
                            if my_id == player1_id:
                                updated_monsters = battle_status.get('player1_monsters', [])
                                opponent_monsters = battle_status.get('player2_monsters', [])
                            else:
                                updated_monsters = battle_status.get('player2_monsters', [])
                                opponent_monsters = battle_status.get('player1_monsters', [])
                            
                            # Sync final state with game manager
                            if updated_monsters:
                                self.game_manager.bag.monsters = updated_monsters
                                print(f"[BATTLE] Final state: My monsters updated: {updated_monsters[0]['name']} HP={updated_monsters[0]['hp']}")
                            
                            # Update BattleOverlay with final opponent state
                            if opponent_monsters:
                                from src.data.bag import Bag
                                fake_bag = Bag()
                                fake_bag.monsters = opponent_monsters
                                self.info['bag'] = fake_bag
                                if 'bush_pokemon' in self.info:
                                    del self.info['bush_pokemon']
                                self.BattleOverlay.set_battle_info(self.info)
                                print(f"[BATTLE] Final state: Opponent monsters: {opponent_monsters[0]['name']} HP={opponent_monsters[0]['hp']}")
                        
                        winner_id = battle_status.get('winner')
                        
                        if winner_id:
                            if winner_id == my_id:
                                self.dialog_messages = ["You won!"]
                                print(f"[BATTLE_END] WIN INFO: Online battle finished - winner_id={winner_id}")
                                self.win = True
                            else:
                                self.dialog_messages = ["You lost!"]
                                print(f"[BATTLE_END] LOSE INFO: Online battle finished - winner_id={winner_id} (not me)")
                                self.lost = True
                        else:
                            # No winner means draw or error
                            self.dialog_messages = ["Battle ended"]
                            print("[BATTLE_END] LOSE INFO: Online battle finished - no winner (draw/error)")
                            self.lost = True
                        
                        self.dialog_page_index = 0
                        self.waiting_for_next_page = True
                        self.DialogOverlay.dialog_text = [self.dialog_messages[0]] if self.dialog_messages else ["Battle ended"]
                        self.battle_ended = True
                        # Will exit after dialog pagination finishes (not timer-based)
                        # Delete battle after we've seen the result
                        self.online_manager.delete_battle(self.battle_id)
                        return
                    
                    current_turn = battle_status.get('turn_count', 0)
                    
                    print(f"[CLIENT] Polling: current_turn={current_turn}, last_turn_count={self.last_turn_count}, waiting={self.waiting_for_opponent}")
                    
                    # Check if new turn has been processed
                    # Only process if turn count increased AND we actually have a turn result
                    # (turn_count > 0 means at least one turn has been processed)
                    if current_turn > self.last_turn_count and current_turn > 0:
                        print(f"[CLIENT] New turn detected! Processing turn {current_turn}")
                        self.last_turn_count = current_turn #update local turn count
                        self.action_submitted = False 
                        self.waiting_for_opponent = False 
                        self.submitting_action = False  #ready for next action
                        
                        # Update local monsters from server with safety checks
                        try:
                            my_id = self.online_manager.player_id
                            player1_id = battle_status.get('player1_id')
                            player2_id = battle_status.get('player2_id')
                            
                            if player1_id is None or player2_id is None:
                                print(f"ERROR: Missing player IDs in battle_status: {battle_status}")
                                self.DialogOverlay.dialog_text = ["Battle data error - missing player IDs"]
                                return
                            
                            if my_id == player1_id:
                                updated_monsters = battle_status.get('player1_monsters', [])
                                opponent_monsters = battle_status.get('player2_monsters', [])
                            else:
                                updated_monsters = battle_status.get('player2_monsters', [])
                                opponent_monsters = battle_status.get('player1_monsters', [])
                            
                            if not updated_monsters or not opponent_monsters:
                                print(f"ERROR: Empty monster lists - my_monsters: {updated_monsters}, opp_monsters: {opponent_monsters}")
                                self.DialogOverlay.dialog_text = ["Battle data error - missing monsters"]
                                return
                            
                            # Sync with game manager
                            self.game_manager.bag.monsters = updated_monsters
                            #print(f"[DEBUG] Turn {current_turn}: My monsters updated: {updated_monsters[0]['name']} HP={updated_monsters[0]['hp']}")
                            #print(f"[DEBUG] Turn {current_turn}: Opponent monsters: {opponent_monsters[0]['name']} HP={opponent_monsters[0]['hp']}")
                            
                            # Update BattleOverlay with new opponent monsters
                            from src.data.bag import Bag
                            fake_bag = Bag()
                            fake_bag.monsters = opponent_monsters
                            
                            # Update info dict with fresh opponent data
                            self.info['bag'] = fake_bag
                            # Remove bush_pokemon if exists (to force using bag)
                            if 'bush_pokemon' in self.info:
                                del self.info['bush_pokemon']
                            
                            #print(f"[DEBUG] Updating BattleOverlay with opponent data: {opponent_monsters[0]['name']}")
                            # Force refresh of BattleOverlay
                            self.BattleOverlay.set_battle_info(self.info)
                        except Exception as e:
                            print(f"ERROR processing battle status: {e}")
                            print(f"Battle status data: {battle_status}")
                            self.DialogOverlay.dialog_text = [f"Error: {str(e)}"]
                            return
                        
                        # Display turn results with pagination
                        turn_result = battle_status.get('last_turn_result', {})
                        self.dialog_messages = []
                        if 'messages' in turn_result:
                            self.dialog_messages.extend(turn_result['messages'])
                        
                        # Check win/loss conditions
                        if not updated_monsters or not opponent_monsters:
                            self.DialogOverlay.dialog_text.append("Battle data error!")
                            self.lost = True
                            self.online_manager.end_battle(self.battle_id)
                            return
                        
                        my_monster = updated_monsters[0]
                        opponent_monster = opponent_monsters[0]
                        
                        # Check win/loss conditions
                        battle_end = False
                        if opponent_monster['hp'] <= 0:
                            self.dialog_messages.append("You won!")
                            print(f"[BATTLE_END] WIN INFO: Online battle - opponent {opponent_monster['name']} HP = 0")
                            self.win = True
                            battle_end = True
                        elif my_monster['hp'] <= 0:
                            self.dialog_messages.append("You lost!")
                            print(f"[BATTLE_END] LOSE INFO: Online battle - my {my_monster['name']} HP = 0")
                            self.lost = True
                            battle_end = True
                        
                        # Check timeout
                        elif battle_status.get('winner'):
                            winner_id = battle_status['winner']
                            if winner_id == my_id:
                                self.dialog_messages.append("Opponent timed out! You won!")
                                print(f"[BATTLE_END] WIN INFO: Online battle - opponent timeout (winner={winner_id})")
                                self.win = True
                            else:
                                self.dialog_messages.append("You timed out! You lost!")
                                print(f"[BATTLE_END] LOSE INFO: Online battle - player timeout (winner={winner_id})")
                                self.lost = True
                            battle_end = True
                        
                        # Trigger delayed exit if battle ended
                        if battle_end:
                            self.dialog_page_index = 0
                            self.waiting_for_next_page = True
                            self.DialogOverlay.dialog_text = [self.dialog_messages[0]] if self.dialog_messages else ["Battle ended"]
                            self.battle_ended = True
                            print(f"[BATTLE] Battle ended, will exit after dialog finishes")
                            # Mark battle as finished on server
                            self.online_manager.end_battle(self.battle_id)
                            # Schedule deletion after delay
                            # (will be called in handle_win/handle_lost)
                            self.should_delete_battle = True
                        else:
                            # Battle continues - go back to OPTIONS to choose next action
                            print(f"[BATTLE] Turn {current_turn} complete, returning to OPTIONS")
                            # Add instruction
                            if self.dialog_messages:
                                self.dialog_messages.append("Choose your next action!")
                            # Set up pagination
                            self.dialog_page_index = 0
                            self.waiting_for_next_page = True
                            self.DialogOverlay.dialog_text = [self.dialog_messages[0]] if self.dialog_messages else ["Choose your action!"]
                            # Don't change state yet, wait for user to read messages
                    else:
                        # Still waiting for new turn
                        if self.waiting_for_opponent:
                            self.DialogOverlay.dialog_text = ["Waiting for opponent..."]
                        else:
                            # Show options while waiting
                            self.DialogOverlay.dialog_text = ["Waiting for turn to process..."]
                
                # Online battle logic ends here, return to avoid offline logic
                return
            
            # ===== 離線戰鬥邏輯 (NPC/WILD) =====
            if Monster is not None and Emonster is not None:
                # 檢查是否剛切換寶可夢（需要執行敵人攻擊）
                if self.just_switched_pokemon and self.doing == 0:
                    # 剛切換寶可夢，顯示訊息並跳到敵人回合
                    self.DialogOverlay.dialog_text = [f"Go! {Monster['name']}!"]
                    self.doing = 1  # 直接跳到敵人回合
                    self.just_switched_pokemon = False  # 清除標記
                    return  # 等待玩家按空格查看訊息
                
                # 檢查是否剛使用道具（需要執行敵人攻擊）
                if self.just_used_item and self.doing == 0:
                    # 剛使用道具，跳到敵人回合
                    self.doing = 1  # 直接跳到敵人回合
                    self.just_used_item = False  # 清除標記
                    # 道具使用訊息已經在上面顯示過了，直接等待空格進入敵人回合
                    return
                
                if self.state == DialogState.BATTLE and not self.waiting_for_next_page:
                # if input_manager.key_pressed(pg.K_SPACE):
                    self.DialogOverlay.dialog_text = []
                    
                    # 玩家回合
                    if self.doing == 0:
                        # 獲取玩家選擇的招式
                        moves = Monster.get('moves', [])
                        if moves and self.selected_move_index < len(moves):
                            selected_move = moves[self.selected_move_index]
                        else:
                            # 預設招式
                            selected_move = {"name": "Tackle", "power": 40, "type": "Normal", "category": "physical"}
                        
                        # 計算傷害
                        damage, messages = calculate_damage(Monster, Emonster, selected_move)
                        Emonster['hp'] = max(0, Emonster['hp'] - damage)
                        
                        # 顯示訊息
                        self.DialogOverlay.dialog_text.extend(messages)
                        self.DialogOverlay.dialog_text.append(f"{Emonster['name']} has {Emonster['hp']}/{Emonster['max_hp']} HP left.")
                        
                        # 檢查敵人是否戰敗
                        if Emonster['hp'] <= 0:
                            self.DialogOverlay.dialog_text.append(f"{Emonster['name']} fainted!")
                            
                            # 對於訓練家戰鬥，嘗試自動切換下一個寶可夢
                            if self.kind == BattleState.NPC:
                                if self._auto_switch_enemy_pokemon():
                                    # 成功切換，繼續戰鬥
                                    self.doing = 0
                                    self.state = DialogState.OPTIONS
                                    return
                                else:
                                    # 沒有可用寶可夢，玩家勝利
                                    self.DialogOverlay.dialog_text.append("You won the battle!")
                                    print(f"[BATTLE_END] WIN INFO: Defeated NPC trainer - all enemy Pokemon fainted")
                                    self.win = True
                                    self.doing += 1
                                    return
                            else:
                                # 野生寶可夢戰鬥，直接勝利
                                print(f"[BATTLE_END] WIN INFO: Defeated wild {Emonster['name']}")
                                self.win = True
                                self.doing += 1
                                return
                        
                        self.doing += 1
                        return
                    
                    # 處理玩家寶可夢戰敗後的切換
                    elif self.doing == 1:
                        if self.win:
                            self.handle_win()
                            self.doing = 0
                            return
                        
                        # 敵人回合
                        enemy_moves = Emonster.get('moves', [])
                        if enemy_moves:
                            enemy_move = random.choice(enemy_moves)
                        else:
                            enemy_move = {"name": "Tackle", "power": 40, "type": "Normal", "category": "physical"}
                        
                        # 計算敵人傷害
                        damage, messages = calculate_damage(Emonster, Monster, enemy_move)
                        Monster['hp'] = max(0, Monster['hp'] - damage)
                        
                        # 顯示訊息
                        self.DialogOverlay.dialog_text.extend(messages)
                        self.DialogOverlay.dialog_text.append(f"{Monster['name']} has {Monster['hp']}/{Monster['max_hp']} HP left.")
                        
                        # 檢查玩家是否戰敗
                        if Monster['hp'] <= 0:
                            self.DialogOverlay.dialog_text.append(f"{Monster['name']} fainted!")
                            
                            # 檢查是否還有其他可用寶可夢
                            monsters = self.game_manager.bag.get_monsters()
                            has_available = any(m['hp'] > 0 for m in monsters[1:])
                            
                            if has_available:
                                # 有可用寶可夢，進入強制切換模式
                                self.doing += 1
                                return
                            else:
                                # 沒有可用寶可夢，玩家戰敗
                                self.DialogOverlay.dialog_text.append("All your Pokemon have fainted!")
                                print(f"[BATTLE_END] LOSE INFO: Offline battle - all player Pokemon fainted")
                                self.lost = True
                                self.doing += 1
                                return
                        
                        self.doing += 1
                        return
                    
                    # 強制切換寶可夢或結束回合
                    else:
                        if self.lost:
                            self.handle_lost()
                            self.doing = 0
                            return
                        
                        # 檢查是否需要強制切換寶可夢
                        monsters = self.game_manager.bag.get_monsters()
                        if monsters[0]['hp'] <= 0:
                            # 需要強制切換
                            self.DialogOverlay.dialog_text = None
                            self.state = DialogState.BATTLE
                            self.options_state = OptionsState.POKEMON
                            self.selected_pokemon_index = 0
                            self._update_pokemon_selection_display(force_switch=True)
                            self.doing = 0  # 重置 doing，切換後回到選項
                            return
                        else:
                            # 回合結束，返回選項
                            self.doing = 0
                            self.state = DialogState.OPTIONS
                            self.DialogOverlay.dialog_text = None
                            return

    @override
    def update(self, dt: float) -> None:
        self.update_content(dt)
        for component in self.components:
            component.update(dt)


    @override
    def draw(self, screen: pg.Surface) -> None:
        for component in self.components:
            component.draw(screen)
    
    def handle_lost(self):
        # Handle lost scenario
        # Delete battle if needed (online battle)
        if self.kind == BattleState.ONLINE_BATTLE and self.should_delete_battle:
            self.online_manager.delete_battle(self.battle_id)
            print(f"[BATTLE] Deleted battle {self.battle_id} on exit")
        # self.game_manager.handle_battle_result(win=False)
        scene_manager.change_scene("game")

    def handle_win(self):
        # Handle win scenario
        # Delete battle if needed (online battle)
        if self.kind == BattleState.ONLINE_BATTLE and self.should_delete_battle:
            self.online_manager.delete_battle(self.battle_id)
            print(f"[BATTLE] Deleted battle {self.battle_id} on exit")
        # Reset battle boosts
        monsters = self.game_manager.bag.get_monsters()
        if monsters:
            for monster in monsters:
                monster['attack_boost'] = 0
                monster['defense_boost'] = 0
        # self.game_manager.handle_battle_result(win=True)
        scene_manager.change_scene("game")
    
    def _update_move_selection_display(self):
        """更新招式選擇介面顯示"""
        monsters = self.game_manager.bag.get_monsters()
        if not monsters:
            self.DialogOverlay.dialog_text = ["No Pokemon available!"]
            return
        
        Monster = monsters[0]
        moves = Monster.get('moves', [])
        
        if not moves:
            # 如果沒有招式，使用預設招式
            moves = [{"name": "Tackle", "power": 40, "type": "Normal", "category": "physical"}]
        
        # 顯示最多2個招式 + Back 選項
        move_texts = []
        for i, move in enumerate(moves[:2]):
            move_name = move.get('name', 'Unknown')
            move_power = move.get('power', 0)
            move_type = move.get('type', 'Normal')
            prefix = "->" if i == self.selected_move_index else " "
            move_texts.append(f"{prefix}{move_name} (Power: {move_power}, Type: {move_type})")
        
        # 添加 Back 選項
        num_moves = len(moves[:2])
        prefix = "->" if self.selected_move_index == num_moves else " "
        move_texts.append(f"{prefix}Back")
        
        self.DialogOverlay.dialog_text = move_texts
    
    def _update_item_selection_display(self):
        """更新物品選擇介面顯示"""
        items = self.game_manager.bag.get_items()
        
        # 過濾出戰鬥中可用的物品：Pokeball 和藥水
        usable_items = []
        for item in items:
            if item['count'] > 0:
                item_name = item['name']
                if 'Pokeball' in item_name or 'Potion' in item_name:
                    usable_items.append(item)
        
        if not usable_items:
            self.DialogOverlay.dialog_text = ["No usable items!", "->Back"]
            return
        
        # 顯示從當前選中位置開始的3個物品（帶邊界檢查）
        item_texts = []
        num_usable = len(usable_items)
        
        # 計算顯示範圍：從 selected_item_index 開始，最多顯示3個
        start_idx = self.selected_item_index
        end_idx = min(start_idx + 3, num_usable)
        
        for i in range(start_idx, end_idx):
            item = usable_items[i]
            item_name = item['name']
            item_count = item['count']
            effect = item.get('effect', '')
            # 箭頭只指向第一個顯示的（當前選中的）
            prefix = "->" if i == self.selected_item_index else "  "
            
            # 顯示物品效果
            effect_desc = ""
            if effect == "heal":
                effect_desc = f"Heal {item.get('value', 0)} HP"
            elif effect == "attack_boost":
                effect_desc = f"+{item.get('value', 0)} Atk"
            elif effect == "defense_boost":
                effect_desc = f"+{item.get('value', 0)} Def"
            
            item_texts.append(f"{prefix}{item_name} x{item_count} ({effect_desc})")
        
        # 添加 Back 選項
        prefix = "->" if self.selected_item_index == num_usable else "  "
        item_texts.append(f"{prefix}Back")
        
        self.DialogOverlay.dialog_text = item_texts
    
    def _update_pokemon_selection_display(self, force_switch=False):
        """更新寶可夢選擇介面顯示"""
        monsters = self.game_manager.bag.get_monsters()
        
        # 過濾掉 HP = 0 和當前使用的寶可夢（第一隻）
        switchable_monsters = []
        for i, monster in enumerate(monsters[1:], start=1):  # 跳過第一隻
            if monster['hp'] > 0:
                switchable_monsters.append((i, monster))
        
        if not switchable_monsters:
            if force_switch:
                # 強制切換但沒有可用寶可夢 = 戰敗
                self.DialogOverlay.dialog_text = ["No Pokemon left to battle!"]
                print("[BATTLE_END] LOSE INFO: _update_pokemon_selection_display - no switchable Pokemon during forced switch")
                self.lost = True
            else:
                self.DialogOverlay.dialog_text = ["No Pokemon to switch!", "->Back"]
            return
        
        # 顯示從當前選中位置開始的3隻寶可夢（帶邊界檢查）
        pokemon_texts = []
        if force_switch:
            pokemon_texts.append("Choose a Pokemon (forced):")
        
        num_switchable = len(switchable_monsters)
        # 計算顯示範圍：從 selected_pokemon_index 開始，最多顯示3隻
        start_idx = self.selected_pokemon_index
        end_idx = min(start_idx + 3, num_switchable)
        
        for i in range(start_idx, end_idx):
            real_idx, monster = switchable_monsters[i]
            name = monster['name']
            hp = monster['hp']
            max_hp = monster['max_hp']
            level = monster['level']
            # 箭頭只指向第一個顯示的（當前選中的）
            prefix = "->" if i == self.selected_pokemon_index else "  "
            pokemon_texts.append(f"{prefix}{name} Lv.{level} (HP: {hp}/{max_hp})")
        
        # 添加 Back 選項（僅非強制切換時）
        if not force_switch:
            # Back 選項的索引是 num_switchable
            prefix = "->" if self.selected_pokemon_index == num_switchable else "  "
            pokemon_texts.append(f"{prefix}Back")
        
        self.DialogOverlay.dialog_text = pokemon_texts
    
    def _switch_player_pokemon(self, target_index):
        """切換玩家的寶可夢"""
        monsters = self.game_manager.bag.get_monsters()
        if target_index < len(monsters) and monsters[target_index]['hp'] > 0:
            # 交換位置
            monsters[0], monsters[target_index] = monsters[target_index], monsters[0]
            # 重新載入 sprite
            self.BattleOverlay.load_sprites()
            print(f"[BATTLE] Switched to {monsters[0]['name']}, reloaded sprites")
            return True
        return False
    
    def _auto_switch_enemy_pokemon(self):
        """自動切換敵人的下一個可用寶可夢"""
        Emonsters = self.info.get('bag', None)
        if not Emonsters:
            return False
        
        enemy_monsters = Emonsters.get_monsters()
        
        # 找到第一個 HP > 0 的寶可夢
        for i in range(1, len(enemy_monsters)):
            if enemy_monsters[i]['hp'] > 0:
                # 交換到第一個位置
                enemy_monsters[0], enemy_monsters[i] = enemy_monsters[i], enemy_monsters[0]
                self.DialogOverlay.dialog_text.append(f"{self.info.get('name', 'Opponent')} sent out {enemy_monsters[0]['name']}!")
                # 重新載入 sprite
                self.BattleOverlay.load_sprites()
                print(f"[BATTLE] Enemy switched to {enemy_monsters[0]['name']}, reloaded sprites")
                return True
        
        # 沒有可用寶可夢了
        return False