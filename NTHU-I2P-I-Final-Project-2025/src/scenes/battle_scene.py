import pygame as pg

from src.utils import GameSettings,Logger
from src.sprites import BackgroundSprite
from src.scenes.scene import Scene
from src.interface.components import Button
from src.overlay.battleDialog_overlay import BattleDialogOverlay
from src.overlay.battleoverlay import BattleOverlay
# from src.overlay.settings_overlay import SettingsOverlay
from src.core.services import scene_manager, sound_manager, input_manager, set_game_manager, get_game_manager, get_online_manager
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
    NAN = 2
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
                # self.handle_win()
                self.kind = BattleState.NOBATTLE
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
            self.handle_win()
            return  
        # print(Emonster)

        if self.state == DialogState.DIALOG:
            if input_manager.key_pressed(pg.K_SPACE):
                self.state = DialogState.OPTIONS
                self.options_state = OptionsState.BATTLE
                self.DialogOverlay.dialog_text = None
                return
        if self.state == DialogState.OPTIONS:
            if self.options_state == OptionsState.BATTLE:
                if input_manager.key_pressed(pg.K_RIGHT) or input_manager.key_pressed(pg.K_d):
                    self.options_state = OptionsState.BAG
                elif input_manager.key_pressed(pg.K_DOWN) or input_manager.key_pressed(pg.K_s):
                    self.options_state = OptionsState.NAN
                elif input_manager.key_pressed(pg.K_k) or input_manager.key_pressed(pg.K_SPACE):
                    # For online battles, only enter BATTLE if not already submitted
                    if self.kind == BattleState.ONLINE_BATTLE and self.action_submitted:
                        # Already submitted, ignore
                        self.DialogOverlay.dialog_textA = "Action already submitted, please wait!"
                        return
                    self.state = DialogState.BATTLE
                    if self.kind != BattleState.ONLINE_BATTLE:
                        self.info['cannot_run'] = True
                    self.DialogOverlay.dialog_text = None
                    return
            elif self.options_state == OptionsState.BAG:
                if input_manager.key_pressed(pg.K_LEFT) or input_manager.key_pressed(pg.K_a):
                    self.options_state = OptionsState.BATTLE
                elif input_manager.key_pressed(pg.K_DOWN) or input_manager.key_pressed(pg.K_s):
                    self.options_state = OptionsState.RUNAWAY
                elif input_manager.key_pressed(pg.K_k) or input_manager.key_pressed(pg.K_SPACE):

                    
                    # For wild battles: Pokeball catching logic
                    if self.kind == BattleState.WILD:
                        for i in items:
                            # print(i['name'])
                            if 'Pokeball' == i['name']:
                                if i['count'] > 0 :
                                    i['count'] -=1
                                    import math
                                    import random
                                    self.DialogOverlay.dialog_textA = f"You used a Pokeball! {i['count']} left."
                                    ballr = 1
                                    status = 1
                                    a = (3* Emonster['max_hp'] - 2 * Emonster['hp']) / (3 * Emonster['max_hp']) * Emonster['catch_rate'] * ballr * status
                                    G = 1048560 / (int(math.sqrt(math.sqrt(16711680 / a))))
                                    nums = [random.randint(0, 65535) for _ in range(4)]
                                    shake = sum(1 for num in nums if num < G)
                                    print(shake)
                                    if shake >= 4:
                                        self.DialogOverlay.dialog_textA += f" Gotcha! {Emonster['name']} was caught!"
                                        self.game_manager.bag.add_monster(Emonster)
                                        # self.state = DialogState.DIALOG
                                        self.win = True
                                        return
                                    # Emonster
                                    # self.state = DialogState.DIALOG
                                else :
                                    self.DialogOverlay.dialog_textA = "No Pokeball left!"
                                break
                        return
                    
                    # For online battles: Use healing/buff items
                    else:
                        # Find usable items (healing, buffs)
                        usable_items = [item for item in items if item['count'] > 0 and 
                                       ('Potion' in item['name'] or 'Strength' in item['name'] or 'Defense' in item['name'])]
                        
                        if not usable_items:
                            self.DialogOverlay.dialog_textA = "No usable items!"
                            return
                        
                        self.state = DialogState.BATTLE
                        self.DialogOverlay.dialog_text = None
                        return
            elif self.options_state == OptionsState.NAN:
                if input_manager.key_pressed(pg.K_UP) or input_manager.key_pressed(pg.K_w):
                    self.options_state = OptionsState.BATTLE
                elif input_manager.key_pressed(pg.K_RIGHT) or input_manager.key_pressed(pg.K_d):
                    self.options_state = OptionsState.RUNAWAY
                elif input_manager.key_pressed(pg.K_k) or input_manager.key_pressed(pg.K_SPACE):
                    pass  # Implement NAN function
            elif self.options_state == OptionsState.RUNAWAY:
                if input_manager.key_pressed(pg.K_UP) or input_manager.key_pressed(pg.K_w):
                    self.options_state = OptionsState.BAG
                elif input_manager.key_pressed(pg.K_LEFT) or input_manager.key_pressed(pg.K_a):
                    self.options_state = OptionsState.NAN
                elif input_manager.key_pressed(pg.K_k) or input_manager.key_pressed(pg.K_SPACE):
                    if self.kind == BattleState.ONLINE_BATTLE:
                        self.DialogOverlay.dialog_textA = "You cannot run away from online battles!"
                        return
                    elif self.kind == BattleState.WILD or (self.kind == BattleState.NPC and not self.info.get("cannot_run", False)):
                        scene_manager.change_scene("game")
            self.DialogOverlay.dialog_text = [
                f'->{i}' if i.replace(" ", "").lower() == self.options_state.name.lower() else i
                for i in ['Battle', 'Bag', 'NAN', 'Run Away']
            ]
            return
        if self.state == DialogState.BATTLE:
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
                        action_type = "attack"
                        action_description = "attack"
                    elif self.options_state == OptionsState.BAG:
                        # Find first usable item
                        usable_items = [item for item in items if item['count'] > 0 and 
                                       ('Potion' in item['name'] or 'Strength' in item['name'] or 'Defense' in item['name'])]
                        if usable_items:
                            action_type = "use_item"
                            action_data = {"item_name": usable_items[0]['name']}
                            action_description = f"use {usable_items[0]['name']}"
                        else:
                            action_type = "attack"  # fallback
                            action_description = "attack"
                    
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
                                self.win = True
                            else:
                                self.dialog_messages = ["You lost!"]
                                self.lost = True
                        else:
                            # No winner means draw or error
                            self.dialog_messages = ["Battle ended"]
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
                    
                    # Check if new turn has been processed
                    # Only process if turn count increased AND we actually have a turn result
                    # (turn_count > 0 means at least one turn has been processed)
                    if current_turn > self.last_turn_count and current_turn > 0:
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
                            self.win = True
                            battle_end = True
                        elif my_monster['hp'] <= 0:
                            self.dialog_messages.append("You lost!")
                            self.lost = True
                            battle_end = True
                        
                        # Check timeout
                        elif battle_status.get('winner'):
                            winner_id = battle_status['winner']
                            if winner_id == my_id:
                                self.dialog_messages.append("Opponent timed out! You won!")
                                self.win = True
                            else:
                                self.dialog_messages.append("You timed out! You lost!")
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
            
            # Offline battle logic (only if not online battle)
            if Monster is not None and Emonster is not None:
                # Offline battle logic (NPC/WILD) - requires key press
                if input_manager.key_pressed(pg.K_SPACE) or self.doing == 0:
                    self.DialogOverlay.dialog_text = []
                    if self.doing == 0 :
                        Emonster['hp'] -= Monster['level']  # Simplified damage calculation
                        if Emonster['hp'] <= 0:
                            Emonster['hp'] = 0
                            self.DialogOverlay.dialog_text.append(f"{Monster['name']} used Tackle! {Emonster['name']} fainted!")
                            self.win = True
                            self.doing += 1
                            return
                        else:
                            self.DialogOverlay.dialog_text.append(f"{Monster['name']} used Tackle! {Emonster['name']} has {Emonster['hp']} HP left.")
                    elif self.doing == 1 :
                        if self.win:
                            self.handle_win()
                            self.doing = 0
                            return
                        Monster['hp'] -= Emonster['level']  # Simplified damage calculation
                        if Monster['hp'] <= 0:
                            Monster['hp'] = 0
                            self.DialogOverlay.dialog_text.append(f" {Emonster['name']} used Tackle! {Monster['name']} fainted!")
                            self.lost = True
                            self.doing += 1
                            return
                        else:
                            self.DialogOverlay.dialog_text.append(f" {Emonster['name']} used Tackle! {Monster['name']} has {Monster['hp']} HP left.")
                    else :
                        if self.lost:
                            self.handle_lost()
                            self.doing = 0 
                            return
                        else :
                            self.doing = 0 
                            self.state = DialogState.OPTIONS
                            self.DialogOverlay.dialog_text = None
                            return
            
                    self.doing += 1

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
        # self.game_manager.handle_battle_result(win=True)
        scene_manager.change_scene("game")