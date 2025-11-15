"""Tool for adding products to the shopping basket."""

from typing import Optional
from pydantic import Field

from atomic_agents import BaseIOSchema, BaseTool, BaseToolConfig

from .datastore import EcommerceDatastore


################
# INPUT SCHEMA #
################
class AddToBasketToolInputSchema(BaseIOSchema):
    """
    Tool for adding products to the shopping basket.
    Specify the product SKU and quantity to add.
    """

    sku: str = Field(..., description="Product SKU (stock keeping unit) to add to basket")
    amount: int = Field(..., description="Quantity of the product to add")


#################
# OUTPUT SCHEMA #
#################
class AddToBasketToolOutputSchema(BaseIOSchema):
    """
    Schema for the output of the AddToBasketTool.
    """

    message: str = Field(..., description="Status message or error description")
    code: str = Field("", description="Error code (empty if successful)")
    status_code: int = Field(200, description="HTTP-like status code (200 = success, 404/400 = error)")


#################
# CONFIGURATION #
#################
class AddToBasketToolConfig(BaseToolConfig):
    """
    Configuration for the AddToBasketTool.
    """

    pass


#####################
# MAIN TOOL & LOGIC #
#####################
class AddToBasketTool(BaseTool[AddToBasketToolInputSchema, AddToBasketToolOutputSchema]):
    """
    Tool for adding products to the shopping basket.

    Attributes:
        input_schema (AddToBasketToolInputSchema): The schema for the input data.
        output_schema (AddToBasketToolOutputSchema): The schema for the output data.
    """

    input_schema = AddToBasketToolInputSchema
    output_schema = AddToBasketToolOutputSchema

    def __init__(self, config: AddToBasketToolConfig = AddToBasketToolConfig(), datastore: Optional[EcommerceDatastore] = None):
        """
        Initializes the AddToBasketTool.

        Args:
            config (AddToBasketToolConfig): Configuration for the tool.
            datastore (Optional[EcommerceDatastore]): Shared datastore instance.
        """
        super().__init__(config)
        self.datastore = datastore or EcommerceDatastore()

    def run(self, params: AddToBasketToolInputSchema) -> AddToBasketToolOutputSchema:
        """
        Executes the AddToBasketTool with the given parameters.

        Args:
            params (AddToBasketToolInputSchema): The input parameters for the tool.

        Returns:
            AddToBasketToolOutputSchema: The result of adding to basket.
        """
        result = self.datastore.add_to_basket(sku=params.sku, amount=params.amount)

        return AddToBasketToolOutputSchema(
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

    console = Console()

    # Initialize the tool with shared datastore
    datastore = EcommerceDatastore()
    tool = AddToBasketTool(datastore=datastore)

    # Test 1: Add GPU to basket
    console.print("\n[bold cyan]Test 1: Add Nvidia H100 to basket[/bold cyan]")
    result1 = tool.run(AddToBasketToolInputSchema(sku="gpu-h100", amount=3))
    console.print(Syntax(result1.model_dump_json(indent=2), "json", theme="monokai"))

    # Test 2: Add another GPU
    console.print("\n[bold cyan]Test 2: Add Nvidia A100 to basket[/bold cyan]")
    result2 = tool.run(AddToBasketToolInputSchema(sku="gpu-a100", amount=4))
    console.print(Syntax(result2.model_dump_json(indent=2), "json", theme="monokai"))

    # Test 3: Add non-existent product (error case)
    console.print("\n[bold cyan]Test 3: Add non-existent product[/bold cyan]")
    result3 = tool.run(AddToBasketToolInputSchema(sku="invalid-sku", amount=1))
    console.print(Syntax(result3.model_dump_json(indent=2), "json", theme="monokai"))

    # Show basket contents
    console.print("\n[bold green]Current basket:[/bold green]")
    console.print(datastore.basket)
