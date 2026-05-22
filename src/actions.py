"""
This module defines the discrete actions an agent can take and the possible
results returned by the environment after validating and executing an action.
"""
from enum import Enum

class Action(str, Enum):
    MOVE_UP = "MOVE_UP"
    MOVE_DOWN = "MOVE_DOWN"
    MOVE_LEFT = "MOVE_LEFT"
    MOVE_RIGHT = "MOVE_RIGHT"
    PICK_UP = "PICK_UP"
    OPEN_DOOR = "OPEN_DOOR"
    WAIT = "WAIT"


class ActionResult(str, Enum):
    SUCCESS = "success"
    BLOCKED_BY_WALL = "blocked_by_wall"
    OUT_OF_BOUNDS = "out_of_bounds"
    PICKED_UP_KEY = "picked_up_key"
    KEY_ALREADY_COLLECTED = "key_already_collected"
    NO_ITEM_HERE = "no_item_here"
    OPENED_DOOR = "opened_door"
    DOOR_REQUIRES_KEY = "door_requires_key"
    NOT_ADJACENT_TO_DOOR = "not_adjacent_to_door"
    GOAL_REACHED = "goal_reached"
    WAITED = "waited"
    INVALID_ACTION = "invalid_action"

MOVE_DELTAS: dict[Action, tuple[int, int]] = {Action.MOVE_UP: (-1, 0),Action.MOVE_DOWN: (1, 0),Action.MOVE_LEFT: (0, -1),Action.MOVE_RIGHT: (0, 1)}

def is_move_action(action: Action) -> bool:
    """Return True if the action changes the agent's grid position."""
    return action in MOVE_DELTAS

def get_allowed_actions() -> list[str]:
    """Return all supported actions as strings for observations and prompts."""
    actions = []
    for action in Action:
        actions.append(action.value)
    return actions

def parse_action(raw_action: str) -> Action | None:
    """
    Convert a raw string into an Action enum.
    Returns None if the provided action is not part of the supported action space. 
    The environment or agent loop can then convert this into an INVALID_ACTION result.
    """
    try:
        return Action(raw_action)
    except ValueError:
        return None