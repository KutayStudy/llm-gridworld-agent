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

def save_demo_log(markdown_file: str, steps: list[dict], summary: dict) -> None:
    """Save a human-readable demo log as a Markdown file."""
    log_path = Path(markdown_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    lines = []
    lines.append("# Demo Run")
    lines.append("")
    lines.append("## Goal")
    lines.append("")
    lines.append("Find the key, open the locked door, and reach the goal tile.")
    lines.append("")
    lines.append("## Result")
    lines.append("")
    lines.append(f"Completed: {str(summary['completed']).lower()}  ")
    lines.append(f"Agent: {summary['agent']}  ")
    lines.append(f"Total steps: {summary['total_steps']}  ")
    lines.append(f"Invalid actions: {summary['invalid_actions']}  ")
    lines.append("")
    lines.append("## Step Trace")
    lines.append("")
    lines.append("| Step | Action | Result | Reason |")
    lines.append("|---:|---|---|---|")

    for step in steps:
        reason = step.get("reason")
        if reason is None:
            reason = ""
        reason = str(reason).replace("|", "/")

        lines.append(f"| {step['step']} | {step['action']} | {step['result']} | {reason} |")

    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append(
        "The agent receives structured observations, chooses one action at a time, "
        "and interacts with the environment only through a constrained action space.")
    lines.append("")
    lines.append(
        "The environment validates every action. Invalid physical actions, such as "
        "walking into walls, return results like `blocked_by_wall` without corrupting "
        "environment state.")
    lines.append("")
    lines.append(
        "The LLM agent maintains an internal memory map built only from observations. "
        "It tracks visited positions, known walls, known empty tiles, blocked moves, "
        "recent positions, and discovered landmarks.")

    with log_path.open("w", encoding="utf-8") as file:
        file.write("\n".join(lines))

    print(f"Saved demo log to {log_path}")