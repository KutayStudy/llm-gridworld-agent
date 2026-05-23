"""Command-line entry point for running GridWorld agents."""

from src.utils.logger import create_step_log, create_summary, save_run_log
import argparse
from src.agents.mock_agent import MockAgent
from src.environment import GridWorldEnvironment
from src.agents.llm_agent import LLMAgent


def create_agent(agent_type: str, environment: GridWorldEnvironment):
    """Create the selected agent."""
    if agent_type == "mock":
        return MockAgent(environment)

    if agent_type == "llm":
        return LLMAgent()

    raise ValueError(f"Unsupported agent type: {agent_type}")


def run_agent(agent_type: str, max_steps: int, log_file: str | None = None) -> None:
    """Run an agent inside the GridWorld environment."""
    env = GridWorldEnvironment()
    agent = create_agent(agent_type, env)

    run_log = []

    print("Initial world:")
    print(env.render())
    print("-" * 40)

    while not env.is_done() and env.step_count < max_steps:
        observation = env.get_observation()
        action = agent.choose_action(observation)
        result = env.step(action)

        reason = getattr(agent, "last_reason", None)

        step_log = create_step_log(
            step=env.step_count,
            agent=agent_type,
            observation=observation,
            action=action.value,
            reason=reason,
            result=result.value,
            completed=env.is_done())

        run_log.append(step_log)

        print(f"Action: {action.value}")

        if reason is not None:
            print(f"Reason: {reason}")

        print(f"Result: {result.value}")
        print(env.render())
        print("-" * 40)

    summary = create_summary(agent=agent_type,completed=env.is_done(),
        total_steps=env.step_count,steps=run_log)
    
    print("Run summary")
    print(f"Agent: {summary['agent']}")
    print(f"Completed: {summary['completed']}")
    print(f"Total steps: {summary['total_steps']}")
    print(f"Invalid actions: {summary['invalid_actions']}")

    if log_file is not None:
        save_run_log(log_file, run_log, summary)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run an agent inside the GridWorld environment.")
    parser.add_argument("--agent",choices=["mock", "llm"],default="mock",help="Agent type to run.")
    parser.add_argument("--max-steps",type=int,default=50,help="Maximum number of environment steps.")
    parser.add_argument("--log-file",type=str,default=None,help="Optional path to save the run log as JSON.")
    args = parser.parse_args()

    try:
        run_agent(agent_type=args.agent,max_steps=args.max_steps,log_file=args.log_file)
    except ValueError as error:
        print(f"Error: {error}")


if __name__ == "__main__":
    main()