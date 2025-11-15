"""
Test script for e-commerce tools

This script tests all the e-commerce tools independently to ensure they work correctly.
"""

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from orchestration_agent.tools.ecommerce import (
    EcommerceDatastore,
    ListProductsTool,
    ListProductsToolConfig,
    ListProductsToolInputSchema,
    AddToBasketTool,
    AddToBasketToolConfig,
    AddToBasketToolInputSchema,
    ViewBasketTool,
    ViewBasketToolConfig,
    ViewBasketToolInputSchema,
    RemoveFromBasketTool,
    RemoveFromBasketToolConfig,
    RemoveFromBasketToolInputSchema,
    CheckoutBasketTool,
    CheckoutBasketToolConfig,
    CheckoutBasketToolInputSchema,
)

console = Console()


def print_result(title: str, result):
    """Print a formatted result."""
    console.print(f"\n[bold cyan]{title}[/bold cyan]")
    syntax = Syntax(result.model_dump_json(indent=2), "json", theme="monokai", line_numbers=False)
    console.print(syntax)


def main():
    """Run tests for all e-commerce tools."""

    console.print(Panel.fit(
        "[bold green]E-Commerce Tools Test Suite[/bold green]",
        border_style="green"
    ))

    # Create shared datastore
    datastore = EcommerceDatastore()

    # Initialize all tools
    list_tool = ListProductsTool(datastore=datastore)
    add_tool = AddToBasketTool(datastore=datastore)
    view_tool = ViewBasketTool(datastore=datastore)
    remove_tool = RemoveFromBasketTool(datastore=datastore)
    checkout_tool = CheckoutBasketTool(datastore=datastore)

    # Test 1: List products with valid limit
    console.print("\n" + "=" * 80)
    console.print("[bold yellow]Test 1: List Products (limit=3)[/bold yellow]")
    result = list_tool.run(ListProductsToolInputSchema(offset=0, limit=3))
    print_result("Result", result)

    # Test 2: List products exceeding limit (should fail)
    console.print("\n" + "=" * 80)
    console.print("[bold yellow]Test 2: List Products (limit=10) - Should Fail[/bold yellow]")
    result = list_tool.run(ListProductsToolInputSchema(offset=0, limit=10))
    print_result("Result", result)

    # Test 3: Add GPUs to basket
    console.print("\n" + "=" * 80)
    console.print("[bold yellow]Test 3: Add GPUs to Basket[/bold yellow]")
    result1 = add_tool.run(AddToBasketToolInputSchema(sku="gpu-h100", amount=3))
    print_result("Add H100", result1)
    result2 = add_tool.run(AddToBasketToolInputSchema(sku="gpu-a100", amount=4))
    print_result("Add A100", result2)

    # Test 4: View basket
    console.print("\n" + "=" * 80)
    console.print("[bold yellow]Test 4: View Basket[/bold yellow]")
    result = view_tool.run(ViewBasketToolInputSchema())
    print_result("Basket Contents", result)

    # Test 5: Checkout with insufficient inventory (should fail)
    console.print("\n" + "=" * 80)
    console.print("[bold yellow]Test 5: Checkout (Should Fail - Insufficient Inventory)[/bold yellow]")
    result = checkout_tool.run(CheckoutBasketToolInputSchema())
    print_result("Checkout Result", result)

    # Test 6: Remove excess from basket
    console.print("\n" + "=" * 80)
    console.print("[bold yellow]Test 6: Remove Excess GPUs[/bold yellow]")
    result = remove_tool.run(RemoveFromBasketToolInputSchema(sku="gpu-a100", amount=1))
    print_result("Remove A100", result)

    # Test 7: View basket after removal
    console.print("\n" + "=" * 80)
    console.print("[bold yellow]Test 7: View Basket After Removal[/bold yellow]")
    result = view_tool.run(ViewBasketToolInputSchema())
    print_result("Updated Basket", result)

    # Test 8: Successful checkout
    console.print("\n" + "=" * 80)
    console.print("[bold yellow]Test 8: Checkout (Should Succeed)[/bold yellow]")
    result = checkout_tool.run(CheckoutBasketToolInputSchema())
    print_result("Checkout Result", result)

    # Test 9: View basket after successful checkout (should be empty)
    console.print("\n" + "=" * 80)
    console.print("[bold yellow]Test 9: View Basket After Checkout (Should Be Empty)[/bold yellow]")
    result = view_tool.run(ViewBasketToolInputSchema())
    print_result("Final Basket", result)

    # Show final inventory
    console.print("\n" + "=" * 80)
    console.print("[bold green]Final Inventory After Purchase:[/bold green]")
    for product in datastore.products:
        if "gpu" in product.sku.lower():
            console.print(f"  🎮 {product.sku}: {product.available} available (was {product.available + (3 if 'h100' in product.sku else 3)})")

    console.print("\n" + "=" * 80)
    console.print("[bold green]✓ All tests completed![/bold green]\n")


if __name__ == "__main__":
    main()
