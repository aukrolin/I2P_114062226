from .managers import InputManager, ResourceManager, SceneManager, SoundManager, GameManager, OnlineManager

input_manager = InputManager()
resource_manager = ResourceManager()
scene_manager = SceneManager()
sound_manager = SoundManager()
_game_manager: GameManager | None = None
_online_manager : OnlineManager | None = None
ids = []

def get_game_manager() -> GameManager:
    global _game_manager
    if _game_manager is None:
        raise RuntimeError("GameManager not initialized")
    return _game_manager

def get_online_manager():
    return OnlineManager()
    # game_manager = get_game_manager()
    # return game_manager.online_manager

def append_ids(id):
    global ids
    ids.append(id)
def get_ids():
    global ids
    return ids

def set_game_manager(save_file: str = "saves/start.json"):
    global _game_manager
    _game_manager = GameManager.load(save_file)
    if _game_manager is None:
        raise RuntimeError(f"Failed to load {save_file}")
    
    