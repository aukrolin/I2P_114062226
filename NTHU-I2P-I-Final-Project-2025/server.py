from server.playerHandler import PlayerHandler
from server.battleHandler import BattleHandler

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
PORT = 8989

PLAYER_HANDLER = PlayerHandler()
PLAYER_HANDLER.start()

BATTLE_HANDLER = BattleHandler()
    
class Handler(BaseHTTPRequestHandler):
    # def log_message(self, fmt, *args):
    #     return

    def do_GET(self):
        if self.path == "/":
            self._json(200, {"status": "ok"})
            return
            
        if self.path == "/register":
            pid = PLAYER_HANDLER.register()
            self._json(200, {"message": "registration successful", "id": pid})
            return

        if self.path == "/players":
            self._json(200, {"players": PLAYER_HANDLER.list_players()})
            return
        
        # Check if player has pending battle
        if self.path.startswith("/battle/check"):
            try:
                query = self.path.split("?")[1] if "?" in self.path else ""
                params = dict(x.split("=") for x in query.split("&") if "=" in x)
                player_id = int(params.get("player_id", -1))
                
                if player_id == -1:
                    self._json(400, {"error": "missing_parameters"})
                    return
                
                battle = BATTLE_HANDLER.get_player_battle(player_id)
                if battle:
                    self._json(200, {
                        "has_battle": True,
                        "battle_id": battle.battle_id,
                        "opponent_id": battle.player1_id if player_id == battle.player2_id else battle.player2_id
                    })
                else:
                    self._json(200, {"has_battle": False})
            except Exception as e:
                self._json(400, {"error": "invalid_request", "message": str(e)})
            return
        
        # Battle status endpoint
        if self.path.startswith("/battle/status"):
            try:
                # Parse query parameters
                query = self.path.split("?")[1] if "?" in self.path else ""
                params = dict(x.split("=") for x in query.split("&") if "=" in x)
                battle_id = params.get("battle_id")
                player_id = int(params.get("player_id", -1))
                
                if not battle_id or player_id == -1:
                    self._json(400, {"error": "missing_parameters"})
                    return
                
                status = BATTLE_HANDLER.get_battle_status(battle_id, player_id)
                if status:
                    self._json(200, status)
                else:
                    self._json(404, {"error": "battle_not_found"})
            except Exception as e:
                self._json(400, {"error": "invalid_request", "message": str(e)})
            return

        self._json(404, {"error": "not_found"})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        try:
            body = self.rfile.read(length)
            data = json.loads(body.decode("utf-8"))
        except Exception:
            self._json(400, {"error": "invalid_json"})
            return
        
        # Update player position
        if self.path == "/players":
            missing = [k for k in ("id", "x", "y", "map", "direction") if k not in data]
            if missing:
                self._json(400, {"error": "bad_fields", "missing": missing})
                return

            try:
                pid = int(data["id"])
                x = float(data["x"])
                y = float(data["y"])
                map_name = str(data["map"])
                direction = str(data["direction"])
                monsters = data.get("monsters", None)  # Optional
                items = data.get("items", None)        # Optional
            except (ValueError, TypeError):
                self._json(400, {"error": "bad_fields"})
                return

            ok = PLAYER_HANDLER.update(pid, x, y, map_name, direction, monsters, items)
            if not ok:
                self._json(404, {"error": "player_not_found"})
                return

            self._json(200, {"success": True})
            return
        
        # Create battle
        if self.path == "/battle/create":
            try:
                player1_id = int(data["player1_id"])
                player2_id = int(data["player2_id"])
                
                # Use provided player1 data if available, otherwise fetch from handler
                if "player1_data" in data:
                    player1_data = data["player1_data"]
                else:
                    player1_info = PLAYER_HANDLER.get_player_data(player1_id)
                    if not player1_info:
                        self._json(404, {"error": "player1_not_found"})
                        return
                    player1_data = {
                        "monsters": player1_info["monsters"],
                        "items": player1_info["items"]
                    }
                
                # Fetch player2 data from handler
                player2_info = PLAYER_HANDLER.get_player_data(player2_id)
                if not player2_info:
                    self._json(404, {"error": "player2_not_found"})
                    return
                
                player2_data = {
                    "monsters": player2_info["monsters"],
                    "items": player2_info["items"]
                }
                
                battle_id = BATTLE_HANDLER.create_battle(
                    player1_id, player2_id,
                    player1_data, player2_data
                )
                
                self._json(200, {
                    "success": True,
                    "battle_id": battle_id,
                    "player2_monsters": player2_info["monsters"],
                    "player2_items": player2_info["items"],
                    "message": "Battle created"
                })
            except Exception as e:
                self._json(400, {"error": "battle_creation_failed", "message": str(e)})
            return
        
        # Submit battle action
        if self.path == "/battle/action":
            try:
                battle_id = data["battle_id"]
                player_id = int(data["player_id"])
                action_type = data["action_type"]
                action_data = data.get("data", {})
                
                ok = BATTLE_HANDLER.submit_action(battle_id, player_id, action_type, action_data)
                if ok:
                    self._json(200, {"success": True, "message": "Action submitted"})
                else:
                    self._json(400, {"error": "action_failed"})
            except Exception as e:
                self._json(400, {"error": "invalid_action", "message": str(e)})
            return
        
        # End battle (mark as finished)
        if self.path == "/battle/end":
            try:
                battle_id = data["battle_id"]
                ok = BATTLE_HANDLER.end_battle(battle_id)
                if ok:
                    self._json(200, {"success": True, "message": "Battle marked as finished"})
                else:
                    self._json(404, {"error": "battle_not_found"})
            except Exception as e:
                self._json(400, {"error": "end_battle_failed", "message": str(e)})
            return
        
        # Delete battle (permanent removal)
        if self.path == "/battle/delete":
            try:
                battle_id = data["battle_id"]
                ok = BATTLE_HANDLER.delete_battle(battle_id)
                if ok:
                    self._json(200, {"success": True, "message": "Battle deleted"})
                else:
                    self._json(404, {"error": "battle_not_found"})
            except Exception as e:
                self._json(400, {"error": "delete_battle_failed", "message": str(e)})
            return

        self._json(404, {"error": "not_found"})

    # Utility for JSON responses
    def _json(self, code: int, obj: object) -> None:
        data = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

if __name__ == "__main__":
    print(f"[Server] Running on localhost with port {PORT}")
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
