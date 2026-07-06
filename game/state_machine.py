"""Game state machine — manages high-level game flow.

States: MENU → ARMORY → BRIEFING → PLAYING → EXTRACTION → VICTORY / GAMEOVER
Each state has enter(), update(dt), and exit() semantics.
"""
from enum import Enum


class GameState(Enum):
    MENU = 'menu'
    ARMORY = 'armory'
    OPTIONS = 'options'
    BRIEFING = 'briefing'
    PLAYING = 'playing'
    EXTRACTION = 'extraction'
    VICTORY = 'victory'
    GAMEOVER = 'gameover'
    PAUSED = 'paused'


class StateMachine:
    """Finite state machine for game flow.

    Usage:
        sm = StateMachine()
        sm.transition(GameState.PLAYING)
        # In game loop:
        sm.current_state  # returns GameState.PLAYING
        sm.update(dt, game)  # calls the state's update function
    """

    def __init__(self):
        self.current_state = GameState.MENU
        self.previous_state = GameState.MENU
        self.state_timer = 0.0  # time in current state
        self._handlers = {}
        self._enter_callbacks = {}
        self._exit_callbacks = {}

    def register_handler(self, state, update_fn):
        """Register an update handler for a state."""
        self._handlers[state] = update_fn

    def register_enter(self, state, fn):
        """Register a callback when entering a state."""
        self._enter_callbacks[state] = fn

    def register_exit(self, state, fn):
        """Register a callback when exiting a state."""
        self._exit_callbacks[state] = fn

    def transition(self, new_state):
        """Transition to a new state."""
        if new_state == self.current_state:
            return

        # Exit callback
        exit_fn = self._exit_callbacks.get(self.current_state)
        if exit_fn:
            exit_fn()

        self.previous_state = self.current_state
        self.current_state = new_state
        self.state_timer = 0.0

        # Enter callback
        enter_fn = self._enter_callbacks.get(new_state)
        if enter_fn:
            enter_fn()

    def update(self, dt, game=None):
        """Update the current state."""
        self.state_timer += dt
        handler = self._handlers.get(self.current_state)
        if handler:
            handler(dt, game)

    @property
    def is_playing(self):
        return self.current_state == GameState.PLAYING

    @property
    def is_extraction(self):
        return self.current_state == GameState.EXTRACTION

    @property
    def is_gameover(self):
        return self.current_state in (GameState.GAMEOVER, GameState.VICTORY)

    @property
    def is_menu(self):
        return self.current_state == GameState.MENU

    @property
    def is_armory(self):
        return self.current_state == GameState.ARMORY

    @property
    def is_options(self):
        return self.current_state == GameState.OPTIONS
