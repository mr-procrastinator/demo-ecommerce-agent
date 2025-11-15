"""Tool for listing products from the e-commerce store."""

from typing import List, Optional
from pydantic import Field

from atomic_agents import BaseIOSchema, BaseTool, BaseToolConfig

from .datastore import EcommerceDatastore, Product


################
# INPUT SCHEMA #
################
class ListProductsToolInputSchema(BaseIOSchema):
    """
    Tool for listing available products from the e-commerce store.
    Supports pagination to handle large product catalogs.
    Returns a list of products with their SKU, name, availability, and price.
    """

    offset: int = Field(0, description="Starting index for pagination (default: 0)")
    limit: int = Field(3, description="Maximum number of products to return")


#################
# OUTPUT SCHEMA #
#################
class ProductSchema(BaseIOSchema):
    """Schema for a single product."""
    sku: str = Field(..., description="Stock keeping unit (product ID)")
    name: str = Field(..., description="Product name")
    available: int = Field(..., description="Available quantity in stock")
    price: int = Field(..., description="Price in cents")


class ListProductsToolOutputSchema(BaseIOSchema):
    """
    Schema for the output of the ListProductsTool.
    """

    products: Optional[List[ProductSchema]] = Field(None, description="List of products (if successful)")
    next_offset: Optional[int] = Field(None, description="Next offset for pagination (-1 if no more products)")
    message: str = Field(..., description="Status message or error description")
    code: str = Field("", description="Error code (empty if successful)")
    status_code: int = Field(200, description="HTTP-like status code (200 = success, 400 = error)")


#################
# CONFIGURATION #
#################
class ListProductsToolConfig(BaseToolConfig):
    """
    Configuration for the ListProductsTool.
    """

    pass


#####################
# MAIN TOOL & LOGIC #
#####################
class ListProductsTool(BaseTool[ListProductsToolInputSchema, ListProductsToolOutputSchema]):
    """
    Tool for listing products from the e-commerce store with pagination support.

    Attributes:
        input_schema (ListProductsToolInputSchema): The schema for the input data.
        output_schema (ListProductsToolOutputSchema): The schema for the output data.
    """

    input_schema = ListProductsToolInputSchema
    output_schema = ListProductsToolOutputSchema

    def __init__(self, config: ListProductsToolConfig = ListProductsToolConfig(), datastore: Optional[EcommerceDatastore] = None):
        """
        Initializes the ListProductsTool.

        Args:
            config (ListProductsToolConfig): Configuration for the tool.
            datastore (Optional[EcommerceDatastore]): Shared datastore instance.
        """
        super().__init__(config)
        self.datastore = datastore or EcommerceDatastore()

    def run(self, params: ListProductsToolInputSchema) -> ListProductsToolOutputSchema:
        """
        Executes the ListProductsTool with the given parameters.

        Args:
            params (ListProductsToolInputSchema): The input parameters for the tool.

        Returns:
            ListProductsToolOutputSchema: The list of products or error message.
        """
        result = self.datastore.list_products(offset=params.offset, limit=params.limit)

        # Check if error occurred
        if "status_code" in result and result["status_code"] != 200:
            return ListProductsToolOutputSchema(
                products=None,
                next_offset=None,
                message=result.get("message", "Unknown error"),
                code=result.get("code", ""),
                status_code=result["status_code"]
            )

        # Success case
        return ListProductsToolOutputSchema(
            products=[ProductSchema(**p) for p in result.get("products", [])],
            next_offset=result.get("next_offset", -1),
            message="Products retrieved successfully",
            code="",
            status_code=200
        )


#################
# EXAMPLE USAGE #
#################
if __name__ == "__main__":
    from rich.console import Console
    from rich.syntax import Syntax

    console = Console()

    # Initialize the tool
    tool = ListProductsTool()

    # Test 1: Normal listing with valid limit
    console.print("\n[bold cyan]Test 1: List products with limit=3[/bold cyan]")
    result1 = tool.run(ListProductsToolInputSchema(offset=0, limit=3))
    console.print(Syntax(result1.model_dump_json(indent=2), "json", theme="monokai"))

    # Test 2: Pagination - next page
    console.print("\n[bold cyan]Test 2: List next page[/bold cyan]")
    result2 = tool.run(ListProductsToolInputSchema(offset=3, limit=3))
    console.print(Syntax(result2.model_dump_json(indent=2), "json", theme="monokai"))

    # Test 3: Exceed limit (should trigger error)
    console.print("\n[bold cyan]Test 3: Exceed limit (limit=10)[/bold cyan]")
    result3 = tool.run(ListProductsToolInputSchema(offset=0, limit=10))
    console.print(Syntax(result3.model_dump_json(indent=2), "json", theme="monokai"))
