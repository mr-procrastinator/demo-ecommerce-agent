"""Tool for viewing the current shopping basket contents."""

from typing import List, Optional
from pydantic import Field

from atomic_agents import BaseIOSchema, BaseTool, BaseToolConfig

from .datastore import EcommerceDatastore


################
# INPUT SCHEMA #
################
class ViewBasketToolInputSchema(BaseIOSchema):
    """
    Tool for viewing the current shopping basket contents.
    Returns all items currently in the basket with their quantities and prices.
    No input parameters required.
    """

    pass  # No input parameters needed


#################
# OUTPUT SCHEMA #
#################
class BasketItemSchema(BaseIOSchema):
    """Schema for a single basket item."""
    sku: str = Field(..., description="Stock keeping unit (product ID)")
    name: str = Field(..., description="Product name")
    quantity: int = Field(..., description="Quantity in basket")
    price: int = Field(..., description="Price per item in cents")


class ViewBasketToolOutputSchema(BaseIOSchema):
    """
    Schema for the output of the ViewBasketTool.
    """

    items: List[BasketItemSchema] = Field(..., description="List of items currently in the basket")


#################
# CONFIGURATION #
#################
class ViewBasketToolConfig(BaseToolConfig):
    """
    Configuration for the ViewBasketTool.
    """

    pass


#####################
# MAIN TOOL & LOGIC #
#####################
class ViewBasketTool(BaseTool[ViewBasketToolInputSchema, ViewBasketToolOutputSchema]):
    """
    Tool for viewing the current shopping basket contents.

    Attributes:
        input_schema (ViewBasketToolInputSchema): The schema for the input data.
        output_schema (ViewBasketToolOutputSchema): The schema for the output data.
    """

    input_schema = ViewBasketToolInputSchema
    output_schema = ViewBasketToolOutputSchema

    def __init__(self, config: ViewBasketToolConfig = ViewBasketToolConfig(), datastore: Optional[EcommerceDatastore] = None):
        """
        Initializes the ViewBasketTool.

        Args:
            config (ViewBasketToolConfig): Configuration for the tool.
            datastore (Optional[EcommerceDatastore]): Shared datastore instance.
        """
        super().__init__(config)
        self.datastore = datastore or EcommerceDatastore()

    def run(self, params: ViewBasketToolInputSchema) -> ViewBasketToolOutputSchema:
        """
        Executes the ViewBasketTool with the given parameters.

        Args:
            params (ViewBasketToolInputSchema): The input parameters for the tool.

        Returns:
            ViewBasketToolOutputSchema: The current basket contents.
        """
        result = self.datastore.view_basket()

        return ViewBasketToolOutputSchema(
            items=[BasketItemSchema(**item) for item in result.get("items", [])]
        )


#################
# EXAMPLE USAGE #
#################
if __name__ == "__main__":
    from rich.console import Console
    from rich.syntax import Syntax
    from .add_to_basket import AddToBasketTool, AddToBasketToolConfig, AddToBasketToolInputSchema

    console = Console()

    # Initialize tools with shared datastore
    datastore = EcommerceDatastore()
    add_tool = AddToBasketTool(datastore=datastore)
    view_tool = ViewBasketTool(datastore=datastore)

    # Add some items to basket
    console.print("\n[bold cyan]Adding items to basket...[/bold cyan]")
    add_tool.run(AddToBasketToolInputSchema(sku="gpu-h100", amount=3))
    add_tool.run(AddToBasketToolInputSchema(sku="gpu-a100", amount=4))

    # View basket
    console.print("\n[bold green]Current basket contents:[/bold green]")
    result = view_tool.run(ViewBasketToolInputSchema())
    console.print(Syntax(result.model_dump_json(indent=2), "json", theme="monokai"))
