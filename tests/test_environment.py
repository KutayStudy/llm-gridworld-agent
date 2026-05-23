"""Tests for GridWorld environment rules."""

from src.actions import Action, ActionResult
from src.environment import GridWorldEnvironment

def move_to_key(env: GridWorldEnvironment) -> None:
    """Move the agent from the start position to the key tile."""
    env.step(Action.MOVE_RIGHT)
    env.step(Action.MOVE_RIGHT)
    env.step(Action.MOVE_RIGHT)

def pick_up_key(env: GridWorldEnvironment) -> None:
    """Move to the key tile and pick up the key."""
    move_to_key(env)
    result = env.step(Action.PICK_UP)
    assert result == ActionResult.PICKED_UP_KEY

def move_next_to_door_without_key(env: GridWorldEnvironment) -> None:
    """Move next to the locked door without collecting the key."""
    env.step(Action.MOVE_RIGHT)
    env.step(Action.MOVE_DOWN)
    env.step(Action.MOVE_DOWN)
    env.step(Action.MOVE_RIGHT)

def move_next_to_door_after_key(env: GridWorldEnvironment) -> None:
    """Collect the key and move next to the locked door."""
    pick_up_key(env)

    env.step(Action.MOVE_LEFT)
    env.step(Action.MOVE_LEFT)
    env.step(Action.MOVE_DOWN)
    env.step(Action.MOVE_DOWN)
    env.step(Action.MOVE_RIGHT)

def open_door(env: GridWorldEnvironment) -> None:
    """Collect the key, move next to the door, and open it."""
    move_next_to_door_after_key(env)
    result = env.step(Action.OPEN_DOOR)
    assert result == ActionResult.OPENED_DOOR

def test_agent_cannot_walk_through_wall() -> None:
    env = GridWorldEnvironment()
    result = env.step(Action.MOVE_UP)
    assert result == ActionResult.BLOCKED_BY_WALL

def test_agent_cannot_move_into_locked_door() -> None:
    env = GridWorldEnvironment()
    move_next_to_door_without_key(env)
    result = env.step(Action.MOVE_DOWN)
    assert result == ActionResult.BLOCKED_BY_WALL

def test_agent_can_move_through_open_door() -> None:
    env = GridWorldEnvironment()
    open_door(env)
    result = env.step(Action.MOVE_DOWN)
    assert result == ActionResult.SUCCESS

def test_agent_can_pick_up_key() -> None:
    env = GridWorldEnvironment()
    move_to_key(env)
    result = env.step(Action.PICK_UP)
    assert result == ActionResult.PICKED_UP_KEY
    assert "key" in env.inventory

def test_agent_cannot_pick_up_key_twice() -> None:
    env = GridWorldEnvironment()
    pick_up_key(env)
    result = env.step(Action.PICK_UP)
    assert result == ActionResult.KEY_ALREADY_COLLECTED

def test_pick_up_on_empty_tile_returns_no_item() -> None:
    env = GridWorldEnvironment()
    result = env.step(Action.PICK_UP)
    assert result == ActionResult.NO_ITEM_HERE

def test_agent_cannot_open_door_before_picking_key() -> None:
    env = GridWorldEnvironment()
    result = env.step(Action.OPEN_DOOR)
    assert result == ActionResult.DOOR_REQUIRES_KEY

def test_agent_cannot_open_door_when_not_adjacent() -> None:
    env = GridWorldEnvironment()
    pick_up_key(env)
    result = env.step(Action.OPEN_DOOR)
    assert result == ActionResult.NOT_ADJACENT_TO_DOOR

def test_agent_can_open_door_after_picking_key() -> None:
    env = GridWorldEnvironment()
    open_door(env)
    assert env.door_open is True

def test_wait_action_returns_waited() -> None:
    env = GridWorldEnvironment()
    result = env.step(Action.WAIT)
    assert result == ActionResult.WAITED

def test_goal_not_reached_before_door_opened() -> None:
    env = GridWorldEnvironment()

    env.step(Action.MOVE_RIGHT)
    env.step(Action.MOVE_RIGHT)
    env.step(Action.MOVE_RIGHT)
    env.step(Action.MOVE_RIGHT)
    env.step(Action.MOVE_RIGHT)
    env.step(Action.MOVE_RIGHT)
    env.step(Action.MOVE_DOWN)
    env.step(Action.MOVE_DOWN)

    result = env.step(Action.MOVE_DOWN)

    assert result != ActionResult.GOAL_REACHED
    assert env.is_done() is False

def test_goal_reached_after_door_opened() -> None:
    env = GridWorldEnvironment()
    open_door(env)
    env.step(Action.MOVE_DOWN)
    env.step(Action.MOVE_DOWN)
    env.step(Action.MOVE_RIGHT)
    env.step(Action.MOVE_RIGHT)
    env.step(Action.MOVE_RIGHT)
    env.step(Action.MOVE_UP)

    result = env.step(Action.MOVE_RIGHT)
    assert result == ActionResult.GOAL_REACHED
    assert env.is_done() is True