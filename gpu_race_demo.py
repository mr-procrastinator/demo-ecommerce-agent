"""
Demo script: GPU Race - Buy ALL GPUs

This script demonstrates the planning agent executing a complex e-commerce task
similar to the behavior shown in the screenshot. The agent will:
1. List all available products (handling pagination)
2. Identify GPU products
3. Add them to the basket
4. Handle inventory errors
5. Adjust basket quantities
6. Complete the checkout
"""

import os
from dotenv import load_dotenv
from orchestration_agent.planning_agent import PlanningExecutor
from orchestration_agent.tools.ecommerce import EcommerceDatastore

load_dotenv()


def main():
    """Run the GPU purchasing demo."""

    print("\n" + "=" * 80)
    print("GPU RACE DEMO - BUY ALL GPUS")
    print("=" * 80)
    print("\n⚠️  RACE CONDITION SIMULATION ENABLED")
    print("During the first checkout, another customer will purchase some GPUs,")
    print("forcing the agent to adjust its basket and retry.\n")

    # Create a shared datastore with race condition simulation
    datastore = EcommerceDatastore(simulate_race_condition=True)

    print("\n[Initial Product Catalog]")
    print("-" * 80)
    for product in datastore.products:
        emoji = "🎮" if "gpu" in product.sku.lower() else "📦"
        print(f"{emoji} {product.sku:15} | {product.name:20} | Available: {product.available:2} | ${product.price/100:.2f}")

    # Create the planning executor
    executor = PlanningExecutor(datastore=datastore)

    # Execute the task: Buy ALL GPUs
    print("\n")
    result = executor.execute_task(task="Buy ALL GPUs", max_steps=20)

    # Show final state
    print("\n[Final State]")
    print("-" * 80)
    print(f"Steps executed: {result['steps']}")
    print(f"Goal achieved: {result['goal_achieved']}")

    print("\n[Final Product Inventory]")
    print("-" * 80)
    for product in datastore.products:
        emoji = "🎮" if "gpu" in product.sku.lower() else "📦"
        print(f"{emoji} {product.sku:15} | {product.name:20} | Available: {product.available:2} | ${product.price/100:.2f}")

    print("\n[Final Basket State]")
    print("-" * 80)
    if datastore.basket:
        for sku, qty in datastore.basket.items():
            product = next((p for p in datastore.products if p.sku == sku), None)
            if product:
                print(f"  {sku}: {qty}x {product.name}")
    else:
        print("  Basket is empty (checkout completed successfully!)")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("\n⚠️  ERROR: OPENAI_API_KEY not found in environment variables!")
        print("Please set your OpenAI API key in .env file or environment.")
        print("Example: export OPENAI_API_KEY='your-key-here'\n")
        exit(1)

    main()
