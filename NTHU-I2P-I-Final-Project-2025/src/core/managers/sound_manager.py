import pygame as pg
from src.utils import load_sound, GameSettings

class SoundManager:
    def __init__(self):
        pg.mixer.init()
        pg.mixer.set_num_channels(GameSettings.MAX_CHANNELS)
        self.current_bgm = None
        self._volume = GameSettings.AUDIO_VOLUME
        self.muted = 1.0  # 1.0 for unmuted, 0.0 for muted

    def play_bgm(self, filepath: str):
        if self.current_bgm:
            self.current_bgm.stop()
        audio = load_sound(filepath)
        audio.set_volume(self.volume * self.muted)
        audio.play(-1)
        self.current_bgm = audio
        
    @property
    def volume(self) -> float:
        return self._volume
    
    @volume.setter
    def volume(self, vol: float):
        self._volume = max(0.0, min(1.0, vol))
        if self.current_bgm:
            self.current_bgm.set_volume(self._volume)

    def set_volume(self, vol: float):
        self.volume = vol

    def mute(self):
        self.muted = 0.0
        if self.current_bgm:
            self.current_bgm.set_volume(0.0)
    def unmute(self):
        self.muted = 1.0
        if self.current_bgm:
            self.current_bgm.set_volume(self._volume)
                


    def pause_all(self):
        pg.mixer.pause()

    def resume_all(self):
        pg.mixer.unpause()
        
    def play_sound(self, filepath):
        
        sound = load_sound(filepath)
        sound.set_volume(self.volume * self.muted)
        sound.play()

    def stop_all_sounds(self):
        pg.mixer.stop()
        self.current_bgm = None