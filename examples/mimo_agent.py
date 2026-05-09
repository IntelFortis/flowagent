"""
MiMo Agent Example

This example demonstrates how to use Xiaomi MiMo model with FlowAgent.

Usage:
    # Option 1: vLLM (recommended for production)
    # First start vLLM server:
    #   pip install vllm
    #   vllm serve XiaomiMiMo/MiMo-7B-RL --host 0.0.0.0 --port 8000
    #
    # Then run this example:
    #   python examples/mimo_agent.py

    # Option 2: Hugging Face (local, requires GPU)
    #   python examples/mimo_agent.py --mode hf
"""

import asyncio
import argparse
from flowagent import Agent, Workflow, task, Context
from flowagent.integrations import MiMo
from flowagent.integrations.llm import LLMMessage


def create_mimo_workflow():
    """Create a workflow that uses MiMo for reasoning tasks."""

    @task
    async def solve_math(ctx: Context):
        """Use MiMo to solve a math problem."""
        llm = MiMo(
            model="XiaomiMiMo/MiMo-7B-RL",
            api_base="http://localhost:8000/v1",
        )

        response = await llm.chat([
            LLMMessage(role="user", content="Solve: What is the derivative of x^3 + 2x^2 - 5x + 7?")
        ])
        return response.content

    @task
    async def explain_solution(ctx: Context):
        """Use MiMo to explain the solution in simple terms."""
        solution = ctx.get("dep:solve_math")

        llm = MiMo(
            model="XiaomiMiMo/MiMo-7B-RL",
            api_base="http://localhost:8000/v1",
        )

        response = await llm.chat([
            LLMMessage(role="system", content="Explain math solutions in simple, easy-to-understand language."),
            LLMMessage(role="user", content=f"Explain this solution:\n{solution}")
        ])
        return response.content

    workflow = Workflow("mimo-math")
    workflow.add(solve_math)
    workflow.add(explain_solution, depends_on=[solve_math])
    return workflow


def create_mimo_agent():
    """Create an agent powered by MiMo."""
    agent = Agent(
        name="mimo-reasoning-agent",
        model="XiaomiMiMo/MiMo-7B-RL",
        system_prompt="You are a helpful reasoning assistant powered by MiMo.",
    )

    @agent.tool
    async def calculate(expression: str) -> str:
        """Calculate a mathematical expression."""
        try:
            result = eval(expression)
            return str(result)
        except Exception as e:
            return f"Error: {e}"

    return agent


async def main():
    parser = argparse.ArgumentParser(description="MiMo Agent Example")
    parser.add_argument(
        "--mode",
        choices=["vllm", "hf"],
        default="vllm",
        help="Inference mode: vllm (API) or hf (local transformers)",
    )
    parser.add_argument(
        "--api-base",
        default="http://localhost:8000/v1",
        help="vLLM API base URL",
    )
    args = parser.parse_args()

    print("=" * 50)
    print("FlowAgent + MiMo Integration Example")
    print("=" * 50)

    # Example 1: Simple chat
    print("\n--- Example 1: Simple Chat ---")
    llm = MiMo(
        model="XiaomiMiMo/MiMo-7B-RL",
        mode=args.mode,
        api_base=args.api_base,
    )

    response = await llm.chat([
        LLMMessage(role="user", content="What is 2 + 2? Think step by step.")
    ])
    print(f"MiMo: {response.content}")
    print(f"Tokens: {response.usage}")

    # Example 2: Workflow with MiMo tasks
    print("\n--- Example 2: MiMo Workflow ---")
    workflow = create_mimo_workflow()
    print(workflow.visualize())

    try:
        results = workflow.run()
        print(f"\nMath solution:\n{results['solve_math']}")
        print(f"\nExplanation:\n{results['explain_solution']}")
    except Exception as e:
        print(f"Workflow error (is vLLM server running?): {e}")

    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
