"""
Simple Workflow Example

This example demonstrates how to create a simple workflow with FlowAgent.
"""

import asyncio
from flowagent import Workflow, task


@task
def extract_data():
    """Extract data from source."""
    print("Extracting data...")
    return {"users": ["Alice", "Bob", "Charlie"]}


@task(retries=2)
async def transform_data(ctx):
    """Transform the extracted data."""
    data = ctx.get("dep:extract_data")
    print(f"Transforming data: {data}")

    # Simulate async work
    await asyncio.sleep(0.1)

    return {
        "transformed_users": [user.upper() for user in data["users"]]
    }


@task
def load_data(ctx):
    """Load data to destination."""
    data = ctx.get("dep:transform_data")
    print(f"Loading data: {data}")
    return {"status": "success", "records": len(data["transformed_users"])}


# Create workflow at module level for CLI discovery
workflow = Workflow("etl-pipeline")
workflow.add(extract_data)
workflow.add(transform_data, depends_on=[extract_data])
workflow.add(load_data, depends_on=[transform_data])


def main():
    # Visualize the workflow
    print(workflow.visualize())
    print("-" * 40)

    # Execute workflow
    results = workflow.run()

    print("\nResults:")
    for task_name, result in results.items():
        print(f"  {task_name}: {result}")


if __name__ == "__main__":
    main()
