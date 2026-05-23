"""Observation models for the GridWorld environment."""

from pydantic import BaseModel

class VisibleTile(BaseModel):
    """Represents one visible tile around the agent."""
    direction: str
    relative_position: list[int]
    absolute_position: list[int]
    type: str


class Observation(BaseModel):
    """Structured observation returned from the environment to the agent."""
    step: int
    position: list[int]
    current_tile: str
    inventory: list[str]
    goal: str
    current_objective: str
    target_position: list[int] | None
    allowed_actions: list[str]
    visible_radius: int
    visibility_mode: str = "radius_based"
    visible_tiles: list[VisibleTile]
    last_action: str | None = None
    last_action_result: str | None = None
    door_open: bool
    done: bool


def build_observation(step: int,
    position: tuple[int, int],
    current_tile: str,
    inventory: list[str],
    goal: str,
    current_objective: str,
    target_position: list[int] | None,
    allowed_actions: list[str],
    visible_radius: int,
    visible_tiles: list[dict],
    last_action: str | None,
    last_action_result: str | None,
    door_open: bool,
    done: bool,) -> dict:
    """
    Build and validate an observation dictionary.
    The environment still returns a plain dict because it will later be passed
    to logs, prompts, and JSON serialization. Pydantic is used here to keep the
    observation structure explicit and validated.
    """

    observation = Observation(
        step=step,
        position=list(position),
        current_tile=current_tile,
        inventory=inventory.copy(),
        goal=goal,
        current_objective=current_objective,
        target_position=list(target_position) if target_position is not None else None,
        allowed_actions=allowed_actions,
        visible_radius=visible_radius,
        visible_tiles=visible_tiles,
        last_action=last_action,
        last_action_result=last_action_result,
        door_open=door_open,
        done=done,
    )

    return observation.model_dump()