"""
Data Pipeline Example

This example demonstrates a more complex data pipeline with FlowAgent.
"""

import asyncio
import random
from datetime import datetime
from flowagent import Workflow, task, Context


@task
async def fetch_api_data(ctx: Context):
    """Fetch data from multiple APIs."""
    print("Fetching data from APIs...")

    # Simulate API calls
    await asyncio.sleep(0.2)

    return {
        "users": [
            {"id": 1, "name": "Alice", "age": 30},
            {"id": 2, "name": "Bob", "age": 25},
            {"id": 3, "name": "Charlie", "age": 35},
        ],
        "timestamp": datetime.now().isoformat(),
    }


@task
async def fetch_database_data(ctx: Context):
    """Fetch data from database."""
    print("Fetching data from database...")

    # Simulate database query
    await asyncio.sleep(0.15)

    return {
        "orders": [
            {"user_id": 1, "amount": 100.50},
            {"user_id": 2, "amount": 200.75},
            {"user_id": 3, "amount": 150.25},
        ],
    }


@task(retries=3, retry_delay=0.5)
async def validate_data(ctx: Context):
    """Validate the fetched data."""
    api_data = ctx.get("dep:fetch_api_data")
    db_data = ctx.get("dep:fetch_database_data")

    print("Validating data...")

    # Simulate validation
    await asyncio.sleep(0.1)

    # Check data integrity
    if not api_data or not db_data:
        raise ValueError("Missing data")

    user_ids = {user["id"] for user in api_data["users"]}
    order_user_ids = {order["user_id"] for order in db_data["orders"]}

    if not order_user_ids.issubset(user_ids):
        raise ValueError("Invalid user IDs in orders")

    return {"valid": True, "user_count": len(user_ids)}


@task
async def enrich_data(ctx: Context):
    """Enrich data with additional information."""
    api_data = ctx.get("dep:fetch_api_data")
    db_data = ctx.get("dep:fetch_database_data")

    print("Enriching data...")

    # Create user lookup
    user_lookup = {user["id"]: user for user in api_data["users"]}

    # Enrich orders with user info
    enriched_orders = []
    for order in db_data["orders"]:
        user = user_lookup.get(order["user_id"], {})
        enriched_orders.append({
            **order,
            "user_name": user.get("name", "Unknown"),
            "user_age": user.get("age", 0),
            "order_date": datetime.now().isoformat(),
        })

    return {"enriched_orders": enriched_orders}


@task
async def generate_report(ctx: Context):
    """Generate a summary report."""
    enriched_data = ctx.get("dep:enrich_data")
    validation = ctx.get("dep:validate_data")

    print("Generating report...")

    orders = enriched_data["enriched_orders"]
    total_amount = sum(order["amount"] for order in orders)

    report = {
        "summary": {
            "total_orders": len(orders),
            "total_amount": total_amount,
            "average_order": total_amount / len(orders) if orders else 0,
            "valid_users": validation["user_count"],
        },
        "orders": orders,
        "generated_at": datetime.now().isoformat(),
    }

    return report


@task
async def save_report(ctx: Context):
    """Save the report to storage."""
    report = ctx.get("dep:generate_report")

    print(f"Saving report with {report['summary']['total_orders']} orders...")

    # Simulate saving to file/database
    await asyncio.sleep(0.1)

    return {
        "status": "saved",
        "path": "/reports/report_2024.json",
        "size": len(str(report)),
    }


@task
async def send_notification(ctx: Context):
    """Send notification about the report."""
    save_result = ctx.get("dep:save_report")
    report = ctx.get("dep:generate_report")

    print(f"Sending notification: Report saved to {save_result['path']}")
    print(f"  Total orders: {report['summary']['total_orders']}")
    print(f"  Total amount: ${report['summary']['total_amount']:.2f}")

    return {"notification_sent": True}


def main():
    # Create workflow
    workflow = Workflow(
        "data-pipeline",
        description="ETL data pipeline with validation and reporting",
    )

    # Add tasks
    workflow.add(fetch_api_data)
    workflow.add(fetch_database_data)
    workflow.add(validate_data, depends_on=[fetch_api_data, fetch_database_data])
    workflow.add(enrich_data, depends_on=[fetch_api_data, fetch_database_data])
    workflow.add(generate_report, depends_on=[enrich_data, validate_data])
    workflow.add(save_report, depends_on=[generate_report])
    workflow.add(send_notification, depends_on=[save_report, generate_report])

    # Visualize workflow
    print(workflow.visualize())
    print("=" * 60)

    # Execute workflow
    results = workflow.run()

    print("\n" + "=" * 60)
    print("Pipeline Results:")
    print(f"  Duration: {workflow.duration:.2f}s")
    print(f"  Status: {workflow.status.value}")
    print(f"  Tasks completed: {len(results)}")


if __name__ == "__main__":
    main()
