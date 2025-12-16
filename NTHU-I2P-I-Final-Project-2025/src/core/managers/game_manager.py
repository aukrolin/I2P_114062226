from __future__ import annotations
from src.utils import Logger, GameSettings, Position, Teleport
import json, os
import pygame as pg
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.maps.map import Map
    from src.entities.player import Player
    from src.entities.enemy_trainer import EnemyTrainer
    from src.data.bag import Bag
    from src.data.settings import Settings

class GameManager:
    # Entities
    player: Player | None
    enemy_trainers: dict[str, list[EnemyTrainer]]
    bag: "Bag"
    
    # Map properties
    current_map_key: str
    maps: dict[str, Map]
    
    # Changing Scene properties
    should_change_map: bool
    next_map: str
    
    def __init__(self, maps: dict[str, Map], start_map: str, 
                 player: Player | None,
                 enemy_trainers: dict[str, list[EnemyTrainer]], 
                 bag: Bag | None = None):
                     
        from src.data.bag import Bag
        from src.data.settings import Settings
        # Game Properties
        self.maps = maps
        self.current_map_key = start_map
        self.player = player
        self.enemy_trainers = enemy_trainers
        self.bag = bag if bag is not None else Bag([], [])
        self.settings = Settings([], [])
        self.should_change_map = False
        self.next_map = ""
        self.should_change_scene : tuple[bool, str, dict[str, any]] = (False, "", {})
        self.need_overlay : str | None = None
    @property
    def current_map(self) -> Map:
        return self.maps[self.current_map_key]
        
    @property
    def current_enemy_trainers(self) -> list[EnemyTrainer]:
        return self.enemy_trainers[self.current_map_key]
        
    @property
    def current_teleporter(self) -> list[Teleport]:
        return self.maps[self.current_map_key].teleporters
    

    def handle_battle_event(self, info: dict[str, any]) -> None:
        
        self.should_change_scene = (True, "battle", info)

    def handle_NPC_event(self, info: dict[str, any]) -> None:
        if info.get("npc_name") is None:
            Logger.error("NPC interaction event missing 'npc_name' info")
            return
        npc_name = info["npc_name"]

        def handle_clerk():
            Logger.info("Handling interaction with clerk NPC")
            self.need_overlay = "clerk_overlay"
            self.NPCbag = info.get("bag", None)
        def handle_joey():
            Logger.info("Handling interaction with Joey NPC")
            self.need_overlay = "joey_overlay"


        if npc_name == "clerk":
            handle_clerk()
        elif npc_name == "joey":
            handle_joey()
        else:
            Logger.warning(f"Unhandled NPC interaction with '{npc_name}'")
            return



        # self.should_change_scene = (True, "npc_interaction", info)


    def handle_bush_event(self) -> None:
        map = self.maps[self.current_map_key]
        player_pos = self.player.position
        prob : dict[str, int]
        prob_meet : int
        prob,prob_meet = map.query_bush_prob(player_pos) 
        assert sum(prob.values()) == 100, "Bush encounter probabilities total 100%"
        

        import random
        if random.randint(1,100) > prob_meet:
            return
        random_num = random.randint(1,100)
        s = 0
        p = None
        for pokemon, probability in prob.items():
            s += probability
            if random_num <= s:
                p = pokemon
                Logger.info(f"Encountered {pokemon} in bush!")
                break
        if p is not None:
            self.should_change_scene = (True, "battle", {"bush_pokemon": {
                "name": "Squirtle",
                "hp": 50,
                "max_hp": 50,
                "level": 15,
                "sprite_path": "menu_sprites/menusprite7.png",
                "catch_rate": 45
              }
              })

    def check_scene_change(self) -> tuple[str, dict[str, any]] | None:
        if self.should_change_scene[0]:
            scene_name = self.should_change_scene[1]
            infos = self.should_change_scene[2]
            self.should_change_scene = (False, "", {})
            return (scene_name, infos)
        return None


    def switch_map(self, target: str, spawnx: int, spawny: int) -> None:
        if target not in self.maps:
            Logger.warning(f"Map '{target}' not loaded; cannot switch.")
            return
        
        self.next_map = (target,spawnx,spawny)
        self.should_change_map = True
            
    def try_switch_map(self) -> None:
        if self.should_change_map:
            self.current_map_key = self.next_map[0]
            self.should_change_map = False
            self.player.position.x = self.next_map[1] * GameSettings.TILE_SIZE
            self.player.position.y = self.next_map[2] * GameSettings.TILE_SIZE
            self.next_map = ""
            
    def check_collision(self, rect: pg.Rect) -> bool:
        if self.maps[self.current_map_key].check_collision(rect):
            return True
        for entity in self.enemy_trainers[self.current_map_key]:
            if rect.colliderect(entity.animation.rect):
                return True
        
        return False
        
    def save(self, path: str) -> None:
        """保存遊戲狀態"""
        try:
            with open(path, "w") as f:
                json.dump(self.to_dict(), f, indent=2)
            Logger.info(f"Game saved to {path}")
        except Exception as e:
            Logger.error(f"Failed to save game: {e}")
             
    @classmethod
    def load(cls, path: str) -> "GameManager | None":   
        if not os.path.exists(path):
            Logger.error(f"No file found: {path}, ignoring load function")
            return None

        with open(path, "r") as f:
            data = json.load(f)
        return cls.from_dict(data)

    def to_dict(self) -> dict[str, object]:
        map_blocks: list[dict[str, object]] = []
        for key, m in self.maps.items():
            block = m.to_dict()
            block["enemy_trainers"] = [t.to_dict() for t in self.enemy_trainers.get(key, [])]
            map_blocks.append(block)
        return {
            "map": map_blocks,
            "current_map": self.current_map_key,
            "player": self.player.to_dict() if self.player is not None else None,
            "bag": self.bag.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "GameManager":
        from src.maps.map import Map
        from src.entities.player import Player
        from src.entities.enemy_trainer import EnemyTrainer
        from src.data.bag import Bag
        
        Logger.info("Loading maps")
        maps_data: list[dict[str, object]] = data["map"]
        maps: dict[str, Map] = {}
        player_spawns: dict[str, Position] = {}
        trainers: dict[str, list[EnemyTrainer]] = {}
        for entry in maps_data:
            path = entry["path"]
            maps[path] = Map.from_dict(entry)
        current_map = data["current_map"]
        gm = cls(
            maps, current_map,
            None,
            trainers,
            bag=None,
        )
        gm.player_spawns = player_spawns
        gm.current_map_key = current_map
        Logger.info("Loading enemy trainers")
        for m in data["map"]:
            raw_data = m["enemy_trainers"]
            gm.enemy_trainers[m["path"]] = [EnemyTrainer.from_dict(t, gm) for t in raw_data]
        
        Logger.info("Loading Player")
        if data.get("player"):
            gm.player = Player.from_dict(data["player"], gm)
        
        Logger.info("Loading bag")
        from src.data.bag import Bag as _Bag
        gm.bag = Bag.from_dict(data.get("bag", {})) if data.get("bag") else _Bag([], [])
        return gm
    
    def pause_game(self) -> None:
        self.player.paused = True
    def resume_game(self) -> None:
        self.player.paused = False