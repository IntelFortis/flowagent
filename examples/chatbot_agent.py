"""
Chatbot Agent Example

This example demonstrates how to create a chatbot agent with FlowAgent.
"""

import asyncio
from flowagent import Agent, Context
from flowagent.integrations import OpenAI


# Create agent with tools
agent = Agent(
    name="chatbot",
    description="A helpful chatbot assistant",
    model="gpt-5.5",
    system_prompt="You are a helpful assistant. Use tools when needed.",
)


@agent.tool
async def search_knowledge_base(query: str) -> str:
    """Search the knowledge base for information."""
    # Simulate knowledge base search
    await asyncio.sleep(0.1)

    knowledge = {
        "python": "Python is a high-level programming language...",
        "flowagent": "FlowAgent is a workflow automation framework...",
        "ai": "Artificial Intelligence is the simulation of human intelligence...",
    }

    for key, value in knowledge.items():
        if key in query.lower():
            return value

    return "I couldn't find specific information about that."


@agent.tool
async def get_current_time() -> str:
    """Get the current time."""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@agent.tool
async def calculate(expression: str) -> str:
    """Calculate a mathematical expression."""
    try:
        # Simple calculator for the demo. Do not expose eval to untrusted input.
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error: {e}"


async def chat_loop():
    """Run the chat loop."""
    print("Chatbot Agent")
    print("=" * 40)
    print("Type 'quit' to exit")
    print()

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        if not user_input:
            continue

        try:
            # Get response from agent
            response = await agent.run(user_input)
            print(f"Agent: {response}")
            print()

        except Exception as e:
            print(f"Error: {e}")
            print()


async def main():
    """Main function."""
    await chat_loop()


if __name__ == "__main__":
    asyncio.run(main())
