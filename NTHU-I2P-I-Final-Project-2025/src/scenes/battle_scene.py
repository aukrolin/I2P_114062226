import pygame as pg

from src.utils import GameSettings
from src.sprites import BackgroundSprite
from src.scenes.scene import Scene
from src.interface.components import Button
from src.overlay.battleDialog_overlay import BattleDialogOverlay
# from src.overlay.settings_overlay import SettingsOverlay
from src.core.services import scene_manager, sound_manager, input_manager, set_game_manager, get_game_manager
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
        self.options_state = OptionsState.BATTLE
        self.components  = [self.background, self.DialogOverlay]

    @override
    def enter(self) -> None:
        sound_manager.play_bgm("RBY 101 Opening (Part 1).ogg")
        self.state = DialogState.DIALOG  # 初始狀態設為對話 
        self.doing = 0
        self.DialogOverlay.dialog_textA = ""
        self.DialogOverlay.dialog_text = ""
        self.win = False
        self.lost = False
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


                # self.DialogOverlay.dialog_text = f"{self.info['name']}'s {Emonster['name']} has no HP left!"
            # print(self.DialogOverlay.dialog_text)
        elif "online_battle" in self.info:
            self.kind = BattleState.ONLINE_BATTLE

        print(f"Entered Battle Scene, Battle with: {self.info}")  # Debug info
        pass

    @override
    def exit(self) -> None:
        pass

    def update_content(self, dt: float) -> None:
        self.DialogOverlay.state = self.state
        self.game_manager = get_game_manager() 
        Monsters = self.game_manager.bag.get_monsters()
        items = self.game_manager.bag.get_items()
        Monster = None
        # print(Monsters)
        Monster = Monsters[0]
        # for i in Monsters:
            # if i["hp"] > 0:
                # Monster = i
                # break
        if self.kind  == BattleState.WILD:
            Emonster = self.info['bush_pokemon']
        elif self.kind == BattleState.NPC:
            Emonsters = self.info['bag'].get_monsters()
            Emonster = Emonsters[0]
            # for i in Emonsters:
                # if i["hp"] > 0:
                    # Emonster = i
                    # break
        elif self.kind == BattleState.ONLINE_BATTLE:
            pass
        elif self.kind == BattleState.NOBATTLE:
            # if self.doing < :
                # self.doing += 1
            # else : 

            self.handle_win()
            
            return  
            pass
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
                    self.state = DialogState.BATTLE
                    self.info['cannot_run'] = True
                    self.DialogOverlay.dialog_text = None
                    return
            elif self.options_state == OptionsState.BAG:
                if input_manager.key_pressed(pg.K_LEFT) or input_manager.key_pressed(pg.K_a):
                    self.options_state = OptionsState.BATTLE
                elif input_manager.key_pressed(pg.K_DOWN) or input_manager.key_pressed(pg.K_s):
                    self.options_state = OptionsState.RUNAWAY
                elif input_manager.key_pressed(pg.K_k) or input_manager.key_pressed(pg.K_SPACE):
                    if self.kind != BattleState.WILD:
                        self.DialogOverlay.dialog_textA = "You can only use items in wild battles!"
                        return
                    for i in items:
                        print(i['name'])
                        if 'Pokeball' == i['name']:
                            if i['count'] > 0 :
                                i['count'] -=1
                                self.DialogOverlay.dialog_textA = f"You used a Pokeball! {i['count']} left."
                            else :
                                self.DialogOverlay.dialog_textA = "No Pokeball left!"
                            break
                        
                    # only implement pokeball for now
                    pass
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
                    if self.kind == BattleState.WILD or (self.kind == BattleState.NPC and not self.info.get("cannot_run", False)):
                        scene_manager.change_scene("game")
            self.DialogOverlay.dialog_text = [
                f'->{i}' if i.replace(" ", "").lower() == self.options_state.name.lower() else i
                for i in ['Battle', 'Bag', 'NAN', 'Run Away']
            ]
            return

        if self.state == DialogState.BATTLE:
            assert Monster is not None, "No available monster to battle!"
            assert Emonster is not None, "No enemy monster to battle!"
            if input_manager.key_pressed(pg.K_SPACE) or self.doing == 0 :
                self.DialogOverlay.dialog_text = []
                if self.doing == 0 :
                    Emonster['hp'] -= Monster['level']  # Simplified damage calculation
                    if Emonster['hp'] <= 0:
                        Emonster['hp'] = 0
                        self.DialogOverlay.dialog_text.append(f"{Monster['name']} used Tackle! {Emonster['name']} fainted!")
                        self.win = True
                        self.doing += 1
                        return
                    else :  self.DialogOverlay.dialog_text.append(f"{Monster['name']} used Tackle! {Emonster['name']} has {Emonster['hp']} HP left.")
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
                    else:  self.DialogOverlay.dialog_text.append(f" {Emonster['name']} used Tackle! {Monster['name']} has {Monster['hp']} HP left.")
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
                

                pass  # Handle battle state updates here

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
        print('lost')
        # self.game_manager.handle_battle_result(win=False)
        scene_manager.change_scene("game")

    def handle_win(self):
        # Handle win scenario
        print('win')
        # self.game_manager.handle_battle_result(win=True)
        scene_manager.change_scene("game")