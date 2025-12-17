import requests
import threading
import time
from src.utils import Logger, GameSettings
POLL_INTERVAL = 0.02

class OnlineManager:
    list_players: list[dict]
    player_id: int
    
    _stop_event: threading.Event
    _thread: threading.Thread | None
    _lock: threading.Lock
    
    def __init__(self):
        self.base: str = GameSettings.ONLINE_SERVER_URL
        self.player_id = -1
        self.list_players = []

        self._thread = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        
        Logger.info("OnlineManager initialized")
        
    def enter(self):
        self.register()
        self.start()
            
    def exit(self):
        self.stop()
        
    def get_list_players(self) -> list[dict]:
        with self._lock:
            return list(self.list_players)

    # ------------------------------------------------------------------
    # Threading and API Calling Below
    # ------------------------------------------------------------------
    def register(self):
        try:
            url = f"{self.base}/register"
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            if resp.status_code == 200:
                from src.core.services import append_ids

                self.player_id = data["id"]
                append_ids(self.player_id)
                Logger.info(f"OnlineManager registered with id={self.player_id}")
            else:
                Logger.error("Registration failed:", data)
        except Exception as e:
            Logger.warning(f"OnlineManager registration error: {e}")
        return

    def create_battle(self, opponent_id: int, my_monsters: list, my_items: list) -> dict:
        """Create a battle with another player (send my data, server fetches opponent data)"""
        try:
            url = f"{self.base}/battle/create"
            body = {
                "player1_id": self.player_id,
                "player2_id": opponent_id,
                "player1_data": {
                    "monsters": my_monsters,
                    "items": my_items
                }
            }
            Logger.info(f"Creating battle: player1={self.player_id}, player2={opponent_id}")
            resp = requests.post(url, json=body, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                Logger.info(f"Battle created successfully: {data.get('battle_id')}")
                return data
            else:
                Logger.error(f"Battle creation failed: {resp.status_code}, response: {resp.text}")
                return {"success": False}
        except Exception as e:
            Logger.error(f"Battle creation error: {e}")
            return {"success": False}
    
    def submit_battle_action(self, battle_id: str, action_type: str, data: dict = None) -> bool:
        """Submit battle action"""
        try:
            url = f"{self.base}/battle/action"
            body = {
                "battle_id": battle_id,
                "player_id": self.player_id,
                "action_type": action_type,
                "data": data or {}
            }
            resp = requests.post(url, json=body, timeout=5)
            if resp.status_code == 200:
                Logger.info(f"Action submitted: {action_type}")
                return True
            else:
                Logger.warning(f"Action submit failed: {resp.status_code}")
                return False
        except Exception as e:
            Logger.warning(f"Action submit error: {e}")
            return False
    
    def get_battle_status(self, battle_id: str) -> dict:
        """Get battle status"""
        if not battle_id:
            Logger.warning("get_battle_status called with empty battle_id")
            return {}
        
        try:
            url = f"{self.base}/battle/status?battle_id={battle_id}&player_id={self.player_id}"
            Logger.info(f"Getting battle status - battle_id: {battle_id}, player_id: {self.player_id}")
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                return resp.json()
            else:
                Logger.warning(f"Get battle status failed: {resp.status_code}, response: {resp.text}, URL: {url}")
                return {}
        except Exception as e:
            Logger.warning(f"Get battle status error: {e}")
            return {}
    
    def check_pending_battle(self) -> dict:
        """Check if there's a pending battle for this player"""
        if self.player_id == -1:
            return {}
        
        try:
            url = f"{self.base}/battle/check?player_id={self.player_id}"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('has_battle'):
                    Logger.info(f"Pending battle found: {data.get('battle_id')}")
                    return data
                return {}
            else:
                Logger.warning(f"Check pending battle failed: {resp.status_code}, response: {resp.text}")
                return {}
        except Exception as e:
            Logger.warning(f"Check pending battle error: {e}")
            return {}
    
    def end_battle(self, battle_id: str) -> bool:
        """Mark battle as finished"""
        try:
            url = f"{self.base}/battle/end"
            body = {"battle_id": battle_id}
            resp = requests.post(url, json=body, timeout=5)
            if resp.status_code == 200:
                Logger.info("Battle marked as finished")
                return True
            else:
                Logger.warning(f"End battle failed: {resp.status_code}")
                return False
        except Exception as e:
            Logger.warning(f"End battle error: {e}")
            return False
    
    def delete_battle(self, battle_id: str) -> bool:
        """Permanently delete a battle"""
        try:
            url = f"{self.base}/battle/delete"
            body = {"battle_id": battle_id}
            resp = requests.post(url, json=body, timeout=5)
            if resp.status_code == 200:
                Logger.info("Battle deleted")
                return True
            else:
                Logger.warning(f"Delete battle failed: {resp.status_code}")
                return False
        except Exception as e:
            Logger.warning(f"Delete battle error: {e}")
            return False

    def update(self, x: float, y: float, map_name: str) -> bool:
        if self.player_id == -1:
            # Try to register again
            return False
        from src.core.services import get_game_manager
        game_manager = get_game_manager()
        player = game_manager.player
        
        # Include monsters and items data in update
        monsters = game_manager.bag.get_monsters()
        items = game_manager.bag.get_items()
        
        url = f"{self.base}/players"
        body = {
            "id": self.player_id, 
            "x": x, 
            "y": y, 
            "map": map_name,
            "direction": player.direction.name,
            "monsters": monsters,
            "items": items
        }
        # print(body)
        try:
            resp = requests.post(url, json=body, timeout=5)
            if resp.status_code == 200:
                return True
            Logger.warning(f"Update failed: {resp.status_code} {resp.text}")
        except Exception as e:
            if self._on_error:
                try:
                    self._on_error(e)
                except Exception:
                    pass
            Logger.warning(f"Online update error: {e}")
        return False

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._loop,
            name="OnlineManagerPoller",
            daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

    def _loop(self) -> None:
        while not self._stop_event.wait(POLL_INTERVAL):
            self._fetch_players()
            
    def _fetch_players(self) -> None:
        try:
            url = f"{self.base}/players"
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            all_players = resp.json().get("players", [])

            pid = self.player_id
            filtered = [p for key, p in all_players.items() if int(key) != pid]
            with self._lock:
                self.list_players = filtered
            
        except Exception as e:
            Logger.warning(f"OnlineManager fetch error: {e}")