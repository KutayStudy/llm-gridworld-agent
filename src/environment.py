"""Deterministic 2D GridWorld environment for the LLM agent harness."""
from src.actions import Action, ActionResult, MOVE_DELTAS, get_allowed_actions, parse_action
from src.observations import build_observation
from src.utils.renderer import render_grid

Position = tuple[int, int]

class GridWorldEnvironment:
    """A small deterministic grid world with a key-door-goal task."""

    DEFAULT_GRID = [
        "##########",
        "#A..K....#",
        "#..##....#",
        "#....#...#",
        "#..D.#.G.#",
        "#........#",
        "##########",
    ]

    EMPTY = "."
    WALL = "#"
    AGENT = "A"
    KEY = "K"
    DOOR = "D"
    GOAL = "G"

    def __init__(self, visible_radius: int = 2):
        self.visible_radius = visible_radius
        self.grid: list[list[str]] = []
        self.agent_position: Position = (0, 0)
        self.key_position: Position | None = None
        self.door_position: Position | None = None
        self.goal_position: Position | None = None
        self.door_open: bool = False
        self.inventory: list[str] = []
        self.step_count: int = 0
        self.last_action: str | None = None
        self.last_action_result: str | None = None
        self.done: bool = False

        self.reset()

    def reset(self) -> None:
        """Reset the environment to its initial state."""
        self.grid = []
        self.inventory = []
        self.key_position = None
        self.door_position = None
        self.goal_position = None
        self.door_open = False
        self.step_count = 0
        self.last_action = None
        self.last_action_result = None
        self.done = False

        for row_index, row in enumerate(self.DEFAULT_GRID):
            grid_row = []
            for col_index, cell in enumerate(row):
                position = (row_index, col_index)
                if cell == self.AGENT:
                    self.agent_position = position
                    grid_row.append(self.EMPTY)
                elif cell == self.KEY:
                    self.key_position = position
                    grid_row.append(self.KEY)
                elif cell == self.DOOR:
                    self.door_position = position
                    grid_row.append(self.DOOR)
                elif cell == self.GOAL:
                    self.goal_position = position
                    grid_row.append(self.GOAL)
                else:
                    grid_row.append(cell)
            self.grid.append(grid_row)

    def step(self, raw_action: Action | str) -> ActionResult:
        """Validate and execute one action in the environment."""
        if self.done:
            return ActionResult.GOAL_REACHED

        if isinstance(raw_action, Action):
            action = raw_action
        else:
            action = parse_action(raw_action)

        if action is None:
            result = ActionResult.INVALID_ACTION
            return self._record_result(str(raw_action), result)

        if action in MOVE_DELTAS:
            result = self._handle_move(action)
        elif action == Action.PICK_UP:
            result = self._handle_pick_up()
        elif action == Action.OPEN_DOOR:
            result = self._handle_open_door()
        elif action == Action.WAIT:
            result = ActionResult.WAITED
        else:
            result = ActionResult.INVALID_ACTION

        return self._record_result(action.value, result)

    def get_observation(self) -> dict:
        """Return a structured observation for an agent."""

        goal = "Find the key, open the locked door, and reach the goal tile."

        observation = build_observation(
            step=self.step_count,
            position=self.agent_position,
            inventory=self.inventory,
            goal=goal,
            allowed_actions=get_allowed_actions(),
            visible_radius=self.visible_radius,
            visible_tiles=self._get_visible_tiles(),
            last_action=self.last_action,
            last_action_result=self.last_action_result,
            door_open=self.door_open,
            done=self.done,)

        return observation

    def is_done(self) -> bool:
        """Return True if the goal task has been completed."""
        return self.done

    def render(self) -> str:
        """Return a human-readable grid representation."""
        return render_grid(
            grid=self.grid,
            agent_position=self.agent_position,
            agent_symbol=self.AGENT,
            step_count=self.step_count,
            inventory=self.inventory,
            door_open=self.door_open,
            last_action=self.last_action,
            last_action_result=self.last_action_result)

    def _handle_move(self, action: Action) -> ActionResult:
        row, col = self.agent_position

        delta_row, delta_col = MOVE_DELTAS[action]

        next_row = row + delta_row
        next_col = col + delta_col
        next_position = (next_row, next_col)

        if not self._is_inside_grid(next_position):
            return ActionResult.OUT_OF_BOUNDS

        next_cell = self._get_cell(next_position)

        if next_cell == self.WALL:
            return ActionResult.BLOCKED_BY_WALL
        elif next_cell == self.DOOR:
            if not self.door_open:
                return ActionResult.BLOCKED_BY_WALL

        self.agent_position = next_position

        if self.agent_position == self.goal_position:
            if self.door_open:
                self.done = True
                return ActionResult.GOAL_REACHED

        return ActionResult.SUCCESS

    def _handle_pick_up(self) -> ActionResult:
        if "key" in self.inventory:
            return ActionResult.KEY_ALREADY_COLLECTED

        if self.key_position is None:
            return ActionResult.NO_ITEM_HERE

        if self.agent_position != self.key_position:
            return ActionResult.NO_ITEM_HERE

        self.inventory.append("key")

        key_row, key_col = self.key_position
        self.grid[key_row][key_col] = self.EMPTY
        self.key_position = None

        return ActionResult.PICKED_UP_KEY

    def _handle_open_door(self) -> ActionResult:
        if "key" not in self.inventory:
            return ActionResult.DOOR_REQUIRES_KEY

        if self.door_position is None:
            return ActionResult.NOT_ADJACENT_TO_DOOR

        is_next_to_door = self._is_adjacent(self.agent_position, self.door_position)

        if not is_next_to_door:
            return ActionResult.NOT_ADJACENT_TO_DOOR

        self.door_open = True

        door_row, door_col = self.door_position
        self.grid[door_row][door_col] = self.EMPTY

        return ActionResult.OPENED_DOOR

    def _record_result(self, action: str, result: ActionResult) -> ActionResult:
        # Invalid actions also count as steps because the agent used one decision cycle.
        self.step_count += 1

        self.last_action = action
        self.last_action_result = result.value

        return result

    def _get_visible_tiles(self) -> list[dict]:
        visible_tiles = []

        agent_row, agent_col = self.agent_position

        start_row = agent_row - self.visible_radius
        end_row = agent_row + self.visible_radius

        start_col = agent_col - self.visible_radius
        end_col = agent_col + self.visible_radius

        for row in range(start_row, end_row+1):
            for col in range(start_col, end_col+1):
                position = (row, col)

                if not self._is_inside_grid(position):
                    continue

                row_distance = abs(row - agent_row)
                col_distance = abs(col - agent_col)
                distance = row_distance + col_distance

                if distance > self.visible_radius:
                    continue

                relative_row = row - agent_row
                relative_col = col - agent_col
                relative_position = (relative_row, relative_col)

                visible_tile = {
                    "direction": self._relative_position_to_direction(relative_position),
                    "relative_position": [relative_row, relative_col],
                    "absolute_position": [row, col],
                    "type": self._describe_cell(position),
                }

                visible_tiles.append(visible_tile)

        return visible_tiles

    def _describe_cell(self, position: Position) -> str:
        if position == self.agent_position:
            return "agent"

        cell = self._get_cell(position)

        if cell == self.WALL:
            return "wall"
        elif cell == self.KEY:
            return "key"
        elif cell == self.DOOR:
            if self.door_open:
                return "open_door"
            else:
                return "locked_door"
        elif cell == self.GOAL:
            return "goal"
        else:
            return "empty"

    def _relative_position_to_direction(self, relative_position: Position) -> str:
        row_delta, col_delta = relative_position

        if row_delta == 0 and col_delta == 0:
            return "current"
        elif row_delta < 0 and col_delta == 0:
            return "north"
        elif row_delta > 0 and col_delta == 0:
            return "south"
        elif row_delta == 0 and col_delta > 0:
            return "east"
        elif row_delta == 0 and col_delta < 0:
            return "west"
        elif row_delta < 0 and col_delta > 0:
            return "north_east"
        elif row_delta < 0 and col_delta < 0:
            return "north_west"
        elif row_delta > 0 and col_delta > 0:
            return "south_east"
        else:
            return "south_west"

    def _is_inside_grid(self, position: Position) -> bool:
        row, col = position

        row_is_valid = 0 <= row and row < len(self.grid)
        col_is_valid = 0 <= col and col < len(self.grid[0])

        if row_is_valid and col_is_valid:
            return True

        return False

    def _get_cell(self, position: Position) -> str:
        row, col = position
        return self.grid[row][col]

    def _is_adjacent(self, first: Position, second: Position) -> bool:
        first_row, first_col = first
        second_row, second_col = second

        row_distance = abs(first_row - second_row)
        col_distance = abs(first_col - second_col)

        total_distance = row_distance + col_distance

        if total_distance == 1:
            return True

        return False