import pygame as pg
from src.data.bag import Bag
from src.overlay.overlay import Overlay
from src.interface.components import Button, Checkbox, Slider
from src.core.services import scene_manager, sound_manager, input_manager, get_game_manager
from src.core import GameManager
from src.utils import GameSettings
from typing import Any, override


class BattleDialogOverlay(Overlay):
    def __init__(self, load_callback = None):
        self.rectcolor = (0, 0 , 0)
        self.is_active = False
        self.game_manager: GameManager | None = None
        self.state = 0 # 初始狀態設為對話
        self.off = None
        self.popup_width = GameSettings.SCREEN_WIDTH
        self.popup_height = GameSettings.SCREEN_HEIGHT * 0.2
        self.popup_x = 0
        self.popup_y = (GameSettings.SCREEN_HEIGHT - self.popup_height)

        # 設定字體
        self.font = pg.font.Font("assets/fonts/Minecraft.ttf", 24)
        self.text_color = (255, 255, 255)
        self.text_padding = 20
        self.dialog_text = ""
        self.dialog_textA = ""
        # self.font_x

    

    def rendertext(self,screen, text, x,y):
        # print(self.state, text)
        # if 
        text= self.font.render(text, True, self.text_color)
        screen.blit(text, (x, y))


    @override
    def update(self, dt: float):
        self.update_content(dt)
        
    @override
    def draw(self, screen):
        from src.scenes.battle_scene import DialogState
        """繪製 overlay 框架"""
        popup_rect = pg.Rect(self.popup_x, self.popup_y, self.popup_width, self.popup_height)
        pg.draw.rect(screen, self.rectcolor, popup_rect)
        
        self.draw_content(screen)
        if self.state == DialogState.DIALOG and self.dialog_text:
            self.rendertext(screen, self.dialog_text, self.popup_x + self.text_padding, self.popup_y + self.text_padding)    
        elif self.state == DialogState.OPTIONS and self.dialog_text:
            if self.dialog_textA:
                self.rendertext(screen, self.dialog_textA, self.popup_x + self.text_padding, self.popup_y + self.text_padding)    

            OPTOFF = GameSettings.SCREEN_WIDTH * 2/3
            offs= [     (GameSettings.SCREEN_WIDTH * 1/18,GameSettings.SCREEN_HEIGHT * 0.0), # 1/3 -> cut into 6
                        (GameSettings.SCREEN_WIDTH * 4/18,GameSettings.SCREEN_HEIGHT * 0.0), # 1/3 -> cut into 6 
                        (GameSettings.SCREEN_WIDTH * 1/18,GameSettings.SCREEN_HEIGHT * 0.1), # 1/3 -> cut into 6
                        (GameSettings.SCREEN_WIDTH * 4/18,GameSettings.SCREEN_HEIGHT * 0.1) # 1/3 -> cut into 6
            ]
            for idx,string in enumerate(self.dialog_text):
                self.rendertext(screen, string, 
                    self.popup_x + self.text_padding + offs[idx][0] + OPTOFF,
                    self.popup_y + self.text_padding + offs[idx][1] + self.text_padding
                )
                # self.rendertext(screen, string, self.popup_x + self.text_padding + self.off[0], self.popup_y + self.text_padding + self.off[1] + self.dialog_text.index(string)*30)
        elif self.state == DialogState.BATTLE and self.dialog_text:
            # print(self.dialog_text)
            for idx,string in enumerate(self.dialog_text):
                    self.rendertext(screen, string, 
                        self.popup_x + self.text_padding,
                        self.popup_y + self.text_padding + idx * 30
                    )
            # print(self.dialog_text)
    def update_content(self, dt: float):
        pass

    def draw_content(self, screen: pg.Surface):
        pass