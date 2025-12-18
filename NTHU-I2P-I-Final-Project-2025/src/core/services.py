from .managers import InputManager, ResourceManager, SceneManager, SoundManager, GameManager, OnlineManager, NavigationManager

input_manager = InputManager()
resource_manager = ResourceManager()
scene_manager = SceneManager()
sound_manager = SoundManager()
_game_manager: GameManager | None = None
_online_manager : OnlineManager | None = None
_navigation_manager: NavigationManager | None = None
ids = []

def get_game_manager() -> GameManager:
    global _game_manager
    if _game_manager is None:
        raise RuntimeError("GameManager not initialized")
    return _game_manager

def get_online_manager():
    global _online_manager
    if _online_manager is None:
        _online_manager = OnlineManager()
        _online_manager.enter()  # Initialize and register
    return _online_manager

def get_navigation_manager():
    global _navigation_manager
    if _navigation_manager is None:
        _navigation_manager = NavigationManager()
    return _navigation_manager

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
    
    