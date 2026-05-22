"""Terminal renderer for the GridWorld environment."""


def render_grid(
    grid: list[list[str]],
    agent_position: tuple[int, int],
    agent_symbol: str,
    step_count: int,
    inventory: list[str],
    door_open: bool,
    last_action: str | None,
    last_action_result: str | None,) -> str:
    """Return a human-readable string representation of the grid world."""
    rendered_grid = []

    for row in grid:
        copied_row = row.copy()
        rendered_grid.append(copied_row)

    agent_row, agent_col = agent_position
    rendered_grid[agent_row][agent_col] = agent_symbol

    lines = []

    status_line = (f"Step: {step_count} | Inventory: {inventory} | Door open: {door_open}")

    last_action_line = (f"Last action: {last_action} | Last result: {last_action_result}")

    lines.append(status_line)
    lines.append(last_action_line)
    lines.append("")

    for row in rendered_grid:
        row_text = "".join(row)
        lines.append(row_text)

    return "\n".join(lines)