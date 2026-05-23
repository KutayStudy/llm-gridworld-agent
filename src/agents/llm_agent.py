"""LLM-powered agent for the GridWorld environment."""
from src.actions import Action, parse_action
from src.agents.base_agent import BaseAgent
from src.llm.client import GeminiClient
from src.llm.prompts import SYSTEM_PROMPT, build_user_prompt

class LLMAgent(BaseAgent):
    """Agent that chooses actions using a Gemini model."""
    def __init__(self, client: GeminiClient | None = None):
        if client is None:
            self.client = GeminiClient()
        else:
            self.client = client

        self.last_reason: str | None = None
        self.known_tiles: dict[tuple[int, int], str] = {}
        self.visited_positions: set[tuple[int, int]] = set()
        self.blocked_moves: set[tuple[tuple[int, int], str]] = set()
        self.recent_positions: list[tuple[int, int]] = []

    def choose_action(self, observation: dict) -> Action:
        """Choose the next action using only the given observation."""
        self._update_memory(observation)
        forced_action = self._get_forced_action(observation)

        if forced_action is not None:
            return forced_action
        
        enriched_observation = self._add_memory_to_observation(observation)
        user_prompt = build_user_prompt(enriched_observation)

        response = self.client.generate_action(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt)

        action_text = response.get("action")
        reason = response.get("reason")

        if reason is not None:
            self.last_reason = str(reason)
        else:
            self.last_reason = None

        if action_text is None:
            self.last_reason = "Model response did not contain an action."
            return Action.WAIT

        action_text = str(action_text)

        allowed_actions = observation.get("allowed_actions", [])

        if action_text not in allowed_actions:
            self.last_reason = f"Model returned unsupported action: {action_text}"
            return Action.WAIT

        action = parse_action(action_text)

        if action is None:
            self.last_reason = f"Could not parse action: {action_text}"
            return Action.WAIT
        
        if self._would_continue_loop(observation, action):
            alternative_action = self._choose_exploration_action(observation)

            if alternative_action is not None:
                self.last_reason = (
                    f"Rejected oscillating action {action.value}; "
                    f"using exploration action {alternative_action.value}.")
                return alternative_action
        
        current_position = tuple(observation.get("position", []))

        if (current_position, action.value) in self.blocked_moves:
            self.last_reason = f"Rejected repeated blocked move: {action.value}"
            alternative_action = self._choose_safe_alternative(observation)

            if alternative_action is not None:
                return alternative_action

            return Action.WAIT

        return action
    
    def _update_memory(self, observation: dict) -> None:
        """Update the agent's internal memory using the latest observation."""
        last_action = observation.get("last_action")
        last_result = observation.get("last_action_result")
        position = observation.get("position")

        if position is not None:
            current_position = tuple(position)
            self.visited_positions.add(current_position)

            self.recent_positions.append(current_position)

            if len(self.recent_positions) > 6:
                self.recent_positions.pop(0)

            if last_action is not None:
                if last_result == "blocked_by_wall":
                    self.blocked_moves.add((current_position, str(last_action)))

        visible_tiles = observation.get("visible_tiles", [])

        for tile in visible_tiles:
            absolute_position = tile.get("absolute_position")
            tile_type = tile.get("type")

            if absolute_position is None:
                continue

            if tile_type is None:
                continue

            position_tuple = tuple(absolute_position)
            self.known_tiles[position_tuple] = str(tile_type)
    
    def _get_forced_action(self, observation: dict) -> Action | None:
        """Apply simple rule-based safeguards using only the observation."""
        inventory = observation.get("inventory", [])
        current_tile = observation.get("current_tile")

        if current_tile == "key":
            if "key" not in inventory:
                self.last_reason = "Standing on the key, so picking it up."
                return Action.PICK_UP

        visible_tiles = observation.get("visible_tiles", [])

        for tile in visible_tiles:
            tile_type = tile.get("type")
            relative_position = tile.get("relative_position")
            if tile_type == "locked_door":
                if "key" in inventory:
                    if relative_position in [[-1, 0], [1, 0], [0, -1], [0, 1]]:
                        self.last_reason = ("Adjacent to the locked door with the key, so opening it.")
                        return Action.OPEN_DOOR

        return None
    
    def _build_memory_summary(self) -> dict:
        """Build a JSON-friendly summary of the agent's internal map."""
        known_walls = []
        known_empty_tiles = []
        known_key_position = None
        known_door_position = None
        known_goal_position = None
        blocked_moves = []

        for position, action in self.blocked_moves:
            blocked_moves.append({"position": list(position),"action": action})

        for position, tile_type in self.known_tiles.items():
            position_as_list = list(position)

            if tile_type == "wall":
                known_walls.append(position_as_list)

            elif tile_type == "empty":
                known_empty_tiles.append(position_as_list)

            elif tile_type == "agent":
                known_empty_tiles.append(position_as_list)

            elif tile_type == "key":
                known_key_position = position_as_list

            elif tile_type == "locked_door":
                known_door_position = position_as_list

            elif tile_type == "open_door":
                known_door_position = position_as_list

            elif tile_type == "goal":
                known_goal_position = position_as_list

        visited_positions = []

        for position in self.visited_positions:
            visited_positions.append(list(position))

        memory_summary = {
            "visited_positions": visited_positions,
            "known_walls": known_walls,
            "known_empty_tiles": known_empty_tiles,
            "known_key_position": known_key_position,
            "known_door_position": known_door_position,
            "known_goal_position": known_goal_position}

        return memory_summary
    
    def _add_memory_to_observation(self, observation: dict) -> dict:
        """Return a copy of the observation enriched with agent memory."""
        enriched_observation = observation.copy()
        enriched_observation["agent_memory"] = self._build_memory_summary()

        return enriched_observation
    
    def _choose_safe_alternative(self, observation: dict) -> Action | None:
        """Choose a simple non-blocked movement action using observation memory."""
        position = observation.get("position")

        if position is None:
            return None

        current_position = tuple(position)
        visible_tiles = observation.get("visible_tiles", [])

        movement_actions = {
            (-1, 0): Action.MOVE_UP,
            (1, 0): Action.MOVE_DOWN,
            (0, -1): Action.MOVE_LEFT,
            (0, 1): Action.MOVE_RIGHT}

        candidates = []

        for tile in visible_tiles:
            relative_position = tile.get("relative_position")
            tile_type = tile.get("type")
            absolute_position = tile.get("absolute_position")

            if relative_position not in [[-1, 0], [1, 0], [0, -1], [0, 1]]:
                continue

            if tile_type in ["wall", "locked_door"]:
                continue

            relative_tuple = tuple(relative_position)
            action = movement_actions.get(relative_tuple)

            if action is None:
                continue

            if (current_position, action.value) in self.blocked_moves:
                continue

            if absolute_position is None:
                continue

            absolute_tuple = tuple(absolute_position)

            was_visited = absolute_tuple in self.visited_positions
            candidates.append((was_visited, action))

        if len(candidates) == 0:
            return None

        candidates.sort(key=lambda item: item[0])

        chosen_action = candidates[0][1]
        self.last_reason = f"Using safe alternative action: {chosen_action.value}"
        return chosen_action
    
    def _would_continue_loop(self, observation: dict, action: Action) -> bool:
        """Return True if the action would continue a recent back-and-forth loop."""
        current_position = observation.get("position")

        if current_position is None:
            return False

        destination = self._get_destination_from_action(observation, action)

        if destination is None:
            return False

        if len(self.recent_positions) < 4:
            return False

        recent_tail = self.recent_positions[-4:]

        if destination in recent_tail:
            return True

        return False


    def _get_destination_from_action(
        self,
        observation: dict,
        action: Action) -> tuple[int, int] | None:
        """Return the destination position for a movement action using visible tiles."""
        movement_relative_positions = {
            Action.MOVE_UP: [-1, 0],
            Action.MOVE_DOWN: [1, 0],
            Action.MOVE_LEFT: [0, -1],
            Action.MOVE_RIGHT: [0, 1]}

        relative_position = movement_relative_positions.get(action)

        if relative_position is None:
            return None

        visible_tiles = observation.get("visible_tiles", [])

        for tile in visible_tiles:
            if tile.get("relative_position") == relative_position:
                absolute_position = tile.get("absolute_position")
                if absolute_position is None:
                    return None
                return tuple(absolute_position)

        return None


    def _choose_exploration_action(self, observation: dict) -> Action | None:
        """Choose a safe neighboring move that reduces loops and favors progress."""
        current_position = observation.get("position")

        if current_position is None:
            return None

        current_position_tuple = tuple(current_position)

        target_position = observation.get("target_position")
        current_objective = observation.get("current_objective")

        current_distance_to_target = 0

        if target_position is not None:
            current_row, current_col = current_position_tuple
            target_row, target_col = target_position
            current_distance_to_target = abs(target_row - current_row) + abs(target_col - current_col)

        movement_actions = {
            (-1, 0): Action.MOVE_UP,
            (1, 0): Action.MOVE_DOWN,
            (0, -1): Action.MOVE_LEFT,
            (0, 1): Action.MOVE_RIGHT,
        }

        candidates = []

        for tile in observation.get("visible_tiles", []):
            relative_position = tile.get("relative_position")
            absolute_position = tile.get("absolute_position")
            tile_type = tile.get("type")

            if relative_position is None:
                continue

            if absolute_position is None:
                continue

            relative_tuple = tuple(relative_position)

            if relative_tuple not in movement_actions:
                continue

            if tile_type in ["wall", "locked_door"]:
                continue

            if tile_type == "goal":
                if current_objective != "go_to_goal":
                    continue

            action = movement_actions[relative_tuple]

            if (current_position_tuple, action.value) in self.blocked_moves:
                continue

            destination = tuple(absolute_position)

            was_visited = destination in self.visited_positions
            is_recent = destination in self.recent_positions[-4:]

            distance_penalty = 0

            if target_position is not None:
                target_row, target_col = target_position
                dest_row, dest_col = destination
                distance_to_target = abs(target_row - dest_row) + abs(target_col - dest_col)
                if distance_to_target > current_distance_to_target:
                    distance_penalty = 3
            else:
                distance_to_target = 0

            candidate_score = (10 if is_recent else 0,5 if was_visited else 0,distance_penalty,distance_to_target)
            candidates.append((candidate_score, action))

        if len(candidates) == 0:
            return None

        candidates.sort(key=lambda item: item[0])

        chosen_action = candidates[0][1]
        return chosen_action