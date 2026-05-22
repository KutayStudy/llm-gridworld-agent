"""
Mock BFS agent for the GridWorld environment.
This agent does not use an LLM. It is used as a deterministic fallback
so the project can be tested without an API key.
"""

from collections import deque
from src.actions import Action, MOVE_DELTAS
from src.agents.base_agent import BaseAgent
from src.environment import GridWorldEnvironment, Position


class MockAgent(BaseAgent):
    """A deterministic BFS-based agent for the key-door-goal task."""

    def __init__(self, environment: GridWorldEnvironment):
        self.environment = environment
        self.planned_actions: deque[Action] = deque()

    def choose_action(self, observation: dict) -> Action:
        """Choose the next action using a simple BFS plan."""
        if len(self.planned_actions) == 0:
            plan = self._build_plan()
            self.planned_actions = deque(plan)

        if len(self.planned_actions) == 0:
            return Action.WAIT

        next_action = self.planned_actions.popleft()
        return next_action

    def _build_plan(self) -> list[Action]:
        """Build a plan based on the current task stage."""
        if "key" not in self.environment.inventory:
            return self._build_plan_to_key()

        if not self.environment.door_open:
            return self._build_plan_to_door()

        return self._build_plan_to_goal()

    def _build_plan_to_key(self) -> list[Action]:
        """Plan a path to the key and then pick it up."""
        if self.environment.key_position is None:
            return [Action.WAIT]

        start = self.environment.agent_position
        target = self.environment.key_position

        path_actions = self._find_path(start, target)

        if path_actions is None:
            return [Action.WAIT]

        path_actions.append(Action.PICK_UP)
        return path_actions

    def _build_plan_to_door(self) -> list[Action]:
        """Plan a path to a tile next to the door and then open it."""
        if self.environment.door_position is None:
            return [Action.WAIT]

        start = self.environment.agent_position
        door_position = self.environment.door_position

        adjacent_positions = self._get_adjacent_positions(door_position)

        best_path = None

        for position in adjacent_positions:
            if not self.environment.is_walkable(position):
                continue

            path = self._find_path(start, position)

            if path is None:
                continue

            if best_path is None:
                best_path = path
            elif len(path) < len(best_path):
                best_path = path

        if best_path is None:
            return [Action.WAIT]

        best_path.append(Action.OPEN_DOOR)
        return best_path

    def _build_plan_to_goal(self) -> list[Action]:
        """Plan a path to the goal tile."""
        if self.environment.goal_position is None:
            return [Action.WAIT]

        start = self.environment.agent_position
        target = self.environment.goal_position

        path_actions = self._find_path(start, target)

        if path_actions is None:
            return [Action.WAIT]

        return path_actions

    def _find_path(self, start: Position, target: Position) -> list[Action] | None:
        """Find the shortest path between two positions using BFS."""
        queue = deque()
        queue.append(start)

        visited = set()
        visited.add(start)

        parent: dict[Position, tuple[Position, Action]] = {}

        while len(queue) > 0:
            current_position = queue.popleft()

            if current_position == target:
                path = self._reconstruct_path(start, target, parent)
                return path

            for action, delta in MOVE_DELTAS.items():
                current_row, current_col = current_position
                delta_row, delta_col = delta

                next_row = current_row + delta_row
                next_col = current_col + delta_col
                next_position = (next_row, next_col)

                if next_position in visited:
                    continue

                if not self.environment.is_walkable(next_position):
                    continue

                visited.add(next_position)
                parent[next_position] = (current_position, action)
                queue.append(next_position)

        return None

    def _reconstruct_path(
        self,
        start: Position,
        target: Position,
        parent: dict[Position, tuple[Position, Action]]) -> list[Action]:
        """Reconstruct the action list after BFS reaches the target."""
        actions = []

        current_position = target

        while current_position != start:
            previous_position, action = parent[current_position]
            actions.append(action)
            current_position = previous_position

        actions.reverse()
        return actions

    def _get_adjacent_positions(self, position: Position) -> list[Position]:
        """Return the non-diagonal neighboring positions around a tile."""
        row, col = position
        adjacent_positions = [(row - 1, col),(row + 1, col),(row, col - 1),(row, col + 1)]
        return adjacent_positions