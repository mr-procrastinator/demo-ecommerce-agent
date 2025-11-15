"""Tool for removing products from the shopping basket."""

from typing import Optional
from pydantic import Field

from atomic_agents import BaseIOSchema, BaseTool, BaseToolConfig

from .datastore import EcommerceDatastore


################
# INPUT SCHEMA #
################
class RemoveFromBasketToolInputSchema(BaseIOSchema):
    """
    Tool for removing products from the shopping basket.
    Specify the product SKU and quantity to remove.
    If the quantity reaches zero or below, the item is removed from the basket.
    """

    sku: str = Field(..., description="Product SKU (stock keeping unit) to remove from basket")
    amount: int = Field(..., description="Quantity of the product to remove")


#################
# OUTPUT SCHEMA #
#################
class RemoveFromBasketToolOutputSchema(BaseIOSchema):
    """
    Schema for the output of the RemoveFromBasketTool.
    """

    message: str = Field(..., description="Status message or error description")
    code: str = Field("", description="Error code (empty if successful)")
    status_code: int = Field(200, description="HTTP-like status code (200 = success, 404 = error)")


#################
# CONFIGURATION #
#################
class RemoveFromBasketToolConfig(BaseToolConfig):
    """
    Configuration for the RemoveFromBasketTool.
    """

    pass


#####################
# MAIN TOOL & LOGIC #
#####################
class RemoveFromBasketTool(BaseTool[RemoveFromBasketToolInputSchema, RemoveFromBasketToolOutputSchema]):
    """
    Tool for removing products from the shopping basket.

    Attributes:
        input_schema (RemoveFromBasketToolInputSchema): The schema for the input data.
        output_schema (RemoveFromBasketToolOutputSchema): The schema for the output data.
    """

    input_schema = RemoveFromBasketToolInputSchema
    output_schema = RemoveFromBasketToolOutputSchema

    def __init__(self, config: RemoveFromBasketToolConfig = RemoveFromBasketToolConfig(), datastore: Optional[EcommerceDatastore] = None):
        """
        Initializes the RemoveFromBasketTool.

        Args:
            config (RemoveFromBasketToolConfig): Configuration for the tool.
            datastore (Optional[EcommerceDatastore]): Shared datastore instance.
        """
        super().__init__(config)
        self.datastore = datastore or EcommerceDatastore()

    def run(self, params: RemoveFromBasketToolInputSchema) -> RemoveFromBasketToolOutputSchema:
        """
        Executes the RemoveFromBasketTool with the given parameters.

        Args:
            params (RemoveFromBasketToolInputSchema): The input parameters for the tool.

        Returns:
            RemoveFromBasketToolOutputSchema: The result of removing from basket.
        """
        result = self.datastore.remove_from_basket(sku=params.sku, amount=params.amount)

        return RemoveFromBasketToolOutputSchema(
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
    remove_tool = RemoveFromBasketTool(datastore=datastore)
    view_tool = ViewBasketTool(datastore=datastore)

    # Add items to basket
    console.print("\n[bold cyan]Adding items to basket...[/bold cyan]")
    add_tool.run(AddToBasketToolInputSchema(sku="gpu-h100", amount=3))
    add_tool.run(AddToBasketToolInputSchema(sku="gpu-a100", amount=4))

    # View basket
    console.print("\n[bold green]Basket before removal:[/bold green]")
    result = view_tool.run(ViewBasketToolInputSchema())
    console.print(Syntax(result.model_dump_json(indent=2), "json", theme="monokai"))

    # Remove some items
    console.print("\n[bold cyan]Removing 2 H100 GPUs...[/bold cyan]")
    remove_result = remove_tool.run(RemoveFromBasketToolInputSchema(sku="gpu-h100", amount=2))
    console.print(Syntax(remove_result.model_dump_json(indent=2), "json", theme="monokai"))

    # View basket again
    console.print("\n[bold green]Basket after removal:[/bold green]")
    result = view_tool.run(ViewBasketToolInputSchema())
    console.print(Syntax(result.model_dump_json(indent=2), "json", theme="monokai"))

    # Try to remove non-existent item (error case)
    console.print("\n[bold cyan]Removing non-existent item...[/bold cyan]")
    error_result = remove_tool.run(RemoveFromBasketToolInputSchema(sku="invalid-sku", amount=1))
    console.print(Syntax(error_result.model_dump_json(indent=2), "json", theme="monokai"))
