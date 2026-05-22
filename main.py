"""Command-line entry point for running GridWorld agents."""

import argparse
from src.agents.mock_agent import MockAgent
from src.environment import GridWorldEnvironment

def run_mock_agent(max_steps: int) -> None:
    """Run the mock BFS agent in the GridWorld environment."""
    env = GridWorldEnvironment()
    agent = MockAgent(env)

    print("Initial world:")
    print(env.render())
    print("-" * 40)

    while not env.is_done() and env.step_count < max_steps:
        observation = env.get_observation()
        action = agent.choose_action(observation)
        result = env.step(action)

        print(f"Action: {action.value}")
        print(f"Result: {result.value}")
        print(env.render())
        print("-" * 40)

    print("Run summary")
    print(f"Completed: {env.is_done()}")
    print(f"Total steps: {env.step_count}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run an agent inside the GridWorld environment.")
    parser.add_argument("--agent",choices=["mock"],default="mock",help="Agent type to run.")
    parser.add_argument("--max-steps",type=int,default=50,help="Maximum number of environment steps.",)
    args = parser.parse_args()

    if args.agent == "mock":
        run_mock_agent(args.max_steps)


if __name__ == "__main__":
    main()