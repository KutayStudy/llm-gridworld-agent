"""Run logging utilities for GridWorld agent executions."""

import json
from pathlib import Path
from src.actions import ActionResult

def create_step_log(
    step: int,
    agent: str,
    observation: dict,
    action: str,
    reason: str | None,
    result: str,
    completed: bool) -> dict:
    """Create a JSON-serializable log entry for one environment step."""
    step_log = {
        "step": step,
        "agent": agent,
        "observation": observation,
        "action": action,
        "reason": reason,
        "result": result,
        "completed": completed}

    return step_log


def count_invalid_actions(steps: list[dict]) -> int:
    """Count invalid actions in a run log."""
    invalid_count = 0

    for step in steps:
        if step["result"] == ActionResult.INVALID_ACTION.value:
            invalid_count += 1

    return invalid_count


def create_summary(agent: str, completed: bool, total_steps: int, steps: list[dict]) -> dict:
    """Create a final run summary."""
    summary = {
        "agent": agent,
        "completed": completed,
        "total_steps": total_steps,
        "invalid_actions": count_invalid_actions(steps)}

    return summary


def save_run_log(log_file: str, steps: list[dict], summary: dict) -> None:
    """Save the full run log as a JSON file."""
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    data = {"summary": summary,"steps": steps}

    with log_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)

    print(f"Saved run log to {log_path}")