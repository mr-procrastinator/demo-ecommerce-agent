"""Tool for checking out the shopping basket."""

from typing import Optional
from pydantic import Field

from atomic_agents import BaseIOSchema, BaseTool, BaseToolConfig

from .datastore import EcommerceDatastore


################
# INPUT SCHEMA #
################
class CheckoutBasketToolInputSchema(BaseIOSchema):
    """
    Tool for checking out the shopping basket.
    Validates inventory availability and completes the purchase.
    If any item in the basket exceeds available inventory, checkout fails with an error.
    On success, the basket is cleared and inventory is updated.
    """

    pass  # No input parameters needed


#################
# OUTPUT SCHEMA #
#################
class CheckoutBasketToolOutputSchema(BaseIOSchema):
    """
    Schema for the output of the CheckoutBasketTool.
    """

    message: str = Field(..., description="Status message or error description")
    code: str = Field("", description="Error code (empty if successful)")
    status_code: int = Field(200, description="HTTP-like status code (200 = success, 400 = error)")


#################
# CONFIGURATION #
#################
class CheckoutBasketToolConfig(BaseToolConfig):
    """
    Configuration for the CheckoutBasketTool.
    """

    pass


#####################
# MAIN TOOL & LOGIC #
#####################
class CheckoutBasketTool(BaseTool[CheckoutBasketToolInputSchema, CheckoutBasketToolOutputSchema]):
    """
    Tool for checking out the shopping basket and completing the purchase.

    Attributes:
        input_schema (CheckoutBasketToolInputSchema): The schema for the input data.
        output_schema (CheckoutBasketToolOutputSchema): The schema for the output data.
    """

    input_schema = CheckoutBasketToolInputSchema
    output_schema = CheckoutBasketToolOutputSchema

    def __init__(self, config: CheckoutBasketToolConfig = CheckoutBasketToolConfig(), datastore: Optional[EcommerceDatastore] = None):
        """
        Initializes the CheckoutBasketTool.

        Args:
            config (CheckoutBasketToolConfig): Configuration for the tool.
            datastore (Optional[EcommerceDatastore]): Shared datastore instance.
        """
        super().__init__(config)
        self.datastore = datastore or EcommerceDatastore()

    def run(self, params: CheckoutBasketToolInputSchema) -> CheckoutBasketToolOutputSchema:
        """
        Executes the CheckoutBasketTool with the given parameters.

        Args:
            params (CheckoutBasketToolInputSchema): The input parameters for the tool.

        Returns:
            CheckoutBasketToolOutputSchema: The result of the checkout attempt.
        """
        result = self.datastore.checkout_basket()

        return CheckoutBasketToolOutputSchema(
            message=result.get("message", "Unknown error"),
            code=result.get("code", ""),
            status_code=result.get("status_code", 200)
        )


#################
# EXAMPLE USAGE #
#################
if __name__ == "__main__":
    from rich.console import Console
    from rich.syntax import Syntax
    from .add_to_basket import AddToBasketTool, AddToBasketToolConfig, AddToBasketToolInputSchema
    from .view_basket import ViewBasketTool, ViewBasketToolConfig, ViewBasketToolInputSchema

    console = Console()

    # Initialize tools with shared datastore
    datastore = EcommerceDatastore()
    add_tool = AddToBasketTool(datastore=datastore)
    checkout_tool = CheckoutBasketTool(datastore=datastore)
    view_tool = ViewBasketTool(datastore=datastore)

    # Test 1: Successful checkout
    console.print("\n[bold cyan]Test 1: Successful checkout[/bold cyan]")
    add_tool.run(AddToBasketToolInputSchema(sku="gpu-h100", amount=2))  # Available: 3
    console.print("[bold green]Basket:[/bold green]")
    console.print(view_tool.run(ViewBasketToolInputSchema()))

    result1 = checkout_tool.run(CheckoutBasketToolInputSchema())
    console.print("[bold green]Checkout result:[/bold green]")
    console.print(Syntax(result1.model_dump_json(indent=2), "json", theme="monokai"))

    # Test 2: Failed checkout - insufficient inventory
    console.print("\n[bold cyan]Test 2: Failed checkout (insufficient inventory)[/bold cyan]")
    add_tool.run(AddToBasketToolInputSchema(sku="gpu-h100", amount=3))  # Only 1 left after first checkout
    add_tool.run(AddToBasketToolInputSchema(sku="gpu-a100", amount=4))  # Available: 4
    console.print("[bold green]Basket:[/bold green]")
    console.print(view_tool.run(ViewBasketToolInputSchema()))

    result2 = checkout_tool.run(CheckoutBasketToolInputSchema())
    console.print("[bold red]Checkout result (should fail):[/bold red]")
    console.print(Syntax(result2.model_dump_json(indent=2), "json", theme="monokai"))

    # Basket should still contain items after failed checkout
    console.print("\n[bold yellow]Basket after failed checkout:[/bold yellow]")
    console.print(view_tool.run(ViewBasketToolInputSchema()))
