import pygame as pg
import threading
import time

from src.scenes.scene import Scene
from src.core import GameManager, OnlineManager
from src.core.services import scene_manager, get_game_manager, set_game_manager, get_online_manager, get_navigation_manager, input_manager
from src.interface.components import Button, Minimap, MapButton
from src.utils import Logger, PositionCamera, GameSettings, Position
from src.core.services import sound_manager
from src.sprites import Sprite, Animation
from src.overlay import BagOverlay, SettingsOverlay, Overlay, ClerkOverlay, JoeyOverlay, FullMapOverlay
# from src
from typing import override

class GameScene(Scene):
    online_manager: OnlineManager | None
    sprite_online: Sprite | Animation


    def __init__(self):
        super().__init__()
        self.show_overlay = False  # 控制是否显示 overlay

        self.overlays : dict[str, Overlay] = {
            'bag': BagOverlay(),
            'settings': SettingsOverlay(lambda id: set_game_manager("saves/game1.json")),
            'clerk_overlay': ClerkOverlay(),
            'joey_overlay': JoeyOverlay(),
            'fullmap': FullMapOverlay(),
        }       
        self.game_manager: GameManager = get_game_manager()
        # Online Manager
        self.online_manager = get_online_manager()

        self.list_online_players : list[dict] = []
        self.battle_check_timer = 0.0  # Timer for checking pending battles
        self.battle_check_interval = 1.0  # Check every 1 second

        for overlay in self.overlays.values():
            overlay.set_close_callback(self.overlay_close)
        self.current_overlay = None

        TS = GameSettings.TILE_SIZE
        px = GameSettings.SCREEN_WIDTH - TS *2
        py = TS 
        self.bag_button = Button(
            "UI/button_backpack.png", "UI/button_backpack_hover.png",
            px+TS/2, py, TS, TS,
            lambda id: self.bag_overlay()
        )
        self.settings_button = Button(
            "UI/button_setting.png", "UI/button_setting_hover.png",
            px-TS, py, TS, TS,
            lambda id: self.settings_overlay()
        )
        self.map_button = MapButton(
            px-TS*2.5, py, TS, TS,
            lambda id: self.map_overlay()
        )
        
        # Initialize minimap
        self.minimap = Minimap()
        
        # Initialize navigation manager
        self.navigation_manager = get_navigation_manager()
    
        


    def bag_overlay(self):
        self.overlay_open()
        self.overlay = 'bag'
        Logger.info('Open bag overlay')
    def settings_overlay(self):
        self.overlay_open()
        self.overlay = 'settings'
        Logger.info('Open settings overlay')
    def map_overlay(self):
        self.overlay_open()
        self.overlay = 'fullmap'
        # Generate map when opening
        if isinstance(self.overlays['fullmap'], FullMapOverlay):
            self.overlays['fullmap'].open()
        Logger.info('Open full map overlay')


    def overlay_open(self):
        self.show_overlay = True
        self.game_manager.pause_game()
    def overlay_close(self, id: int = 0):
        self.show_overlay = False
        self.overlay = None
        self.game_manager.resume_game()

    


    
    @override
    def enter(self) -> None:
        sound_manager.play_bgm("RBY 103 Pallet Town.ogg")
        if self.online_manager:
            if not self.game_manager.registered:
                self.online_manager.enter()
            else :
                self.online_manager.start()
            self.game_manager.registered = True
        
    @override
    def exit(self) -> None:
        if self.online_manager:
            self.online_manager.exit()
        
    @override
    def update(self, dt: float):
        # Check if there is assigned next scene
        self.game_manager = get_game_manager()
        self.game_manager.try_switch_map()
        scene_change = self.game_manager.check_scene_change()
        if scene_change:
            scene_manager.change_scene(*scene_change)
            return
        # Update player and other data
        if self.game_manager.player:
            self.game_manager.player.update(dt)
        for enemy in self.game_manager.current_enemy_trainers:
            enemy.update(dt)
            
        # Update others
        self.bag_button.update(dt)
        self.settings_button.update(dt)
        self.map_button.update(dt)
        self.minimap.update(dt)  # Update minimap timer
        
        # Update navigation (auto-move player)
        if self.navigation_manager.active and self.game_manager.player:
            self.navigation_manager.update(self.game_manager.player, dt)
        
        # Navigation controls (only when active)
        if self.navigation_manager.active:
            # ESC to cancel navigation
            if input_manager.key_pressed(pg.K_ESCAPE):
                self.navigation_manager.cancel()
            # N key to toggle speed
            elif input_manager.key_pressed(pg.K_n):
                speed = self.navigation_manager.toggle_speed()
                Logger.info(f"Navigation speed: {speed}x")
            # Manual movement cancels navigation
            elif (input_manager.key_down(pg.K_w) or input_manager.key_down(pg.K_UP) or
                  input_manager.key_down(pg.K_s) or input_manager.key_down(pg.K_DOWN) or
                  input_manager.key_down(pg.K_a) or input_manager.key_down(pg.K_LEFT) or
                  input_manager.key_down(pg.K_d) or input_manager.key_down(pg.K_RIGHT)):
                Logger.info("Navigation cancelled by manual movement")
                self.navigation_manager.cancel()        
        # TEMPORARY: Test navigation with M key (navigate to first teleporter)
        if input_manager.key_pressed(pg.K_m) and self.game_manager.player:
            teleporters = self.game_manager.current_map.teleporters
            if teleporters:
                from src.utils.pathfinding import PathfindingGrid, a_star, pixel_to_tile, tile_to_pixel
                
                # Get player position
                player_tile = pixel_to_tile(
                    int(self.game_manager.player.position.x),
                    int(self.game_manager.player.position.y)
                )
                
                # Get first teleporter position
                target_tp = teleporters[0]
                target_tile = pixel_to_tile(
                    int(target_tp.pos.x),
                    int(target_tp.pos.y)
                )
                
                Logger.info(f"Testing navigation: {player_tile} -> {target_tile}")
                
                # Build pathfinding grid
                map_width_tiles = self.game_manager.current_map.tmxdata.width
                map_height_tiles = self.game_manager.current_map.tmxdata.height
                collision_map = self.game_manager.current_map._collision_map
                
                grid = PathfindingGrid(map_width_tiles, map_height_tiles, collision_map)
                
                # Find path
                tile_path = a_star(grid, player_tile, target_tile)
                # print(tile_path)
                if tile_path:
                    # Convert to pixel coordinates (center of tiles)
                    
                    # Start navigation
                    self.navigation_manager.start_navigation(tile_path, "Test Teleporter")
                    Logger.info(f"Navigation started with {len(tile_path)} waypoints")
                else:
                    Logger.warning("No path found to teleporter!")
        if self.game_manager.need_overlay:
            self.overlay_open()
            self.overlay = self.game_manager.need_overlay
            self.overlays[self.overlay].update_overlay({"bag": self.game_manager.NPCbag})          
            # Logger.info(f'Open {self.overlay} overlay')   
        

        if self.show_overlay and self.overlay:
            self.overlays[self.overlay].update(dt)
            self.game_manager.need_overlay = None
        
        # Check for pending battles periodically
        self.battle_check_timer += dt
        if self.battle_check_timer >= self.battle_check_interval:
            self.battle_check_timer = 0.0
            pending_battle = self.online_manager.check_pending_battle()
            print(f"[BATTLE CHECK] Checking pending battle for player_id={self.online_manager.player_id}: {pending_battle}")
            if pending_battle.get('has_battle'):
                battle_id = pending_battle.get('battle_id')
                opponent_id = pending_battle.get('opponent_id')
                Logger.info(f"Auto-joining battle {battle_id} with opponent {opponent_id}")
                
                # Prepare battle info with existing battle_id
                battle_info = {
                    "online_battle": {
                        "opponent_id": opponent_id,
                        "battle_id": battle_id,  # Use existing battle
                        "is_joiner": True  # Mark as joining player
                    }
                }
                
                # Change to battle scene
                
                scene_manager.change_scene("battle", battle_info)
                return
        
         # Update online manager

        self.list_online_players = self.online_manager.get_list_players()
        self.game_manager.update_online_players(self.list_online_players)

        if self.game_manager.player is not None and self.online_manager is not None:
            _ = self.online_manager.update(
                self.game_manager.player.position.x, 
                self.game_manager.player.position.y,
                self.game_manager.current_map.path_name
            )
            
            # Check for collision with online players FIRST (higher priority than NPC)
            if input_manager.key_pressed(pg.K_k):
                player_rect = self.game_manager.player.animation.rect
                
                # Check online players first
                for idx, online_player_rect in enumerate(self.game_manager.players_collision_map):
                    if player_rect.colliderect(online_player_rect):
                        # Found collision with online player - PREVENT NPC battle
                        opponent = self.list_online_players[idx]
                        opponent_id = opponent.get("id")
                        
                        if opponent_id:
                            Logger.info(f"Triggering online battle with player {opponent_id}")
                            
                            # Prepare battle info (server will fetch monsters/items)
                            battle_info = {
                                "online_battle": {
                                    "opponent_id": opponent_id
                                }
                            }
                            
                            # Change to battle scene immediately
                            scene_manager.change_scene("battle", battle_info)
                            return  # IMPORTANT: Return to prevent NPC battle trigger
                        
                        if opponent_id:
                            Logger.info(f"Triggering online battle with player {opponent_id}")
                            
                            # Prepare battle info (server will fetch monsters/items)
                            battle_info = {
                                "online_battle": {
                                    "opponent_id": opponent_id
                                }
                            }
                            
                            # Change to battle scene
                            scene_manager.change_scene("battle", battle_info)
                            return
        
    @override
    def draw(self, screen: pg.Surface):        
        if self.game_manager.player:
            '''
            [TODO HACKATHON 3]
            Implement the camera algorithm logic here
            Right now it's hard coded, you need to follow the player's positions
            you may use the below example, but the function still incorrect, you may trace the entity.py
            
            camera = self.game_manager.player.camera
            '''
            P = self.game_manager.player
            camera = P.camera
            self.game_manager.current_map.draw(screen, camera)
            self.game_manager.player.draw(screen, camera)
        else:
            camera = PositionCamera(0, 0)
            self.game_manager.current_map.draw(screen, camera)
        for enemy in self.game_manager.current_enemy_trainers:
            enemy.draw(screen, camera)
        for player in self.game_manager.players_collision_map:
            r = player.copy()
            r.left += 4
            r.top += 4
            pg.draw.rect(screen, (255, 0, 0), camera.transform_rect(r), 1)
        if self.show_overlay:
            # 创建半透明黑色遮罩
            overlay_surface = pg.Surface((GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT))
            overlay_surface.set_alpha(128)  # 0-255，128 是半透明
            overlay_surface.fill((0, 0, 0))  # 黑色
            screen.blit(overlay_surface, (0, 0))
            self.overlays[self.overlay].draw(screen)



        self.bag_button.draw(screen)
        self.settings_button.draw(screen)
        self.map_button.draw(screen)
        
         # Draw online players



        if self.online_manager and self.game_manager.player:
            # list_online = self.online_manager.get_list_players()
            for player in self.list_online_players:
                if player["map"] == self.game_manager.current_map.path_name:
                    cam = self.game_manager.player.camera
                    pos = cam.transform_position_as_position(Position(player["x"], player["y"]))
                    # import random
                    # print(player)
                    # continue
                    A = player["Animation"] 
                    self.sprite_online = Animation(
                        A[0], ["down", "left", "right", "up"], 4,
                        (GameSettings.TILE_SIZE, GameSettings.TILE_SIZE)
                    )
                    self.sprite_online.switch(A[1])
                    
                    self.sprite_online.update_pos(pos)
                    
                    self.sprite_online.draw(screen)
        
        # Draw minimap (always on top)
        if self.game_manager.player and not self.show_overlay: #only draw when no overlay like bag/settings/large map   
            # Prepare NPC data
            npc_data = []
            for enemy in self.game_manager.current_enemy_trainers:
                npc_data.append({
                    'x': enemy.position.x,
                    'y': enemy.position.y
                })
            
            # Draw minimap with all elements
            self.minimap.draw(
                screen=screen,
                player_pos=self.game_manager.player.position,
                collision_map=self.game_manager.current_map._collision_map,
                other_players=self.list_online_players,
                npcs=npc_data,
                teleporters=self.game_manager.current_map.teleporters,
                current_map_name=self.game_manager.current_map.path_name
            )
            
            # Draw navigation path on minimap if active
            if self.navigation_manager.active:
                remaining_path = self.navigation_manager.get_remaining_path()
                if remaining_path:
                    # print(remaining_path)
                    # Convert to tile coordinates
                    from src.utils.pathfinding import pixel_to_tile
                    tile_path = [pixel_to_tile(x, y) for x, y in remaining_path]
                    self.minimap.draw_navigation_path(
                        screen, 
                        self.game_manager.player.position, 
                        tile_path
                    )
