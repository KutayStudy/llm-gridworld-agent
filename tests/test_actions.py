"""Tests for action parsing and action helpers."""

from src.actions import Action, get_allowed_actions, is_move_action, parse_action

def test_parse_valid_action() -> None:
    action = parse_action("MOVE_RIGHT")
    assert action == Action.MOVE_RIGHT


def test_parse_invalid_action_returns_none() -> None:
    action = parse_action("JUMP")
    assert action is None


def test_get_allowed_actions_contains_expected_actions() -> None:
    allowed_actions = get_allowed_actions()
    assert "MOVE_UP" in allowed_actions
    assert "MOVE_DOWN" in allowed_actions
    assert "MOVE_LEFT" in allowed_actions
    assert "MOVE_RIGHT" in allowed_actions
    assert "PICK_UP" in allowed_actions
    assert "OPEN_DOOR" in allowed_actions
    assert "WAIT" in allowed_actions


def test_is_move_action() -> None:
    assert is_move_action(Action.MOVE_UP) is True
    assert is_move_action(Action.MOVE_DOWN) is True
    assert is_move_action(Action.MOVE_LEFT) is True
    assert is_move_action(Action.MOVE_RIGHT) is True
    assert is_move_action(Action.PICK_UP) is False
    assert is_move_action(Action.OPEN_DOOR) is False
    assert is_move_action(Action.WAIT) is False