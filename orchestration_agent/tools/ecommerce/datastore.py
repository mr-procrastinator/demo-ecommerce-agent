"""Mock datastore for e-commerce operations."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class Product(BaseModel):
    """Product model."""
    sku: str = Field(..., description="Stock keeping unit (product ID)")
    name: str = Field(..., description="Product name")
    available: int = Field(..., description="Available quantity in stock")
    price: int = Field(..., description="Price in cents")


class BasketItem(BaseModel):
    """Basket item model."""
    sku: str = Field(..., description="Stock keeping unit (product ID)")
    name: str = Field(..., description="Product name")
    quantity: int = Field(..., description="Quantity in basket")
    price: int = Field(..., description="Price per item in cents")


class EcommerceDatastore:
    """
    Mock datastore for e-commerce operations.
    Simulates a product catalog and shopping basket.
    """

    def __init__(self, simulate_race_condition: bool = True):
        """
        Initialize the datastore with mock products.

        Args:
            simulate_race_condition: If True, simulates a race condition where
                                    inventory decreases before first checkout
        """
        # Product catalog - similar to screenshot
        self.products: List[Product] = [
            # Remote control units (not GPUs)
            Product(sku="rc-1200", name="Remote Control Unit", available=10, price=2500),

            # GPUs - these are what we want to buy
            Product(sku="gpu-h100", name="Nvidia H100", available=3, price=20000),
            Product(sku="gpu-a100", name="Nvidia A100", available=4, price=11950),
            Product(sku="mb-450", name="Motherboard X45", available=7, price=500),

            # More products for pagination testing
            Product(sku="cpu-001", name="Intel Xeon", available=15, price=3500),
            Product(sku="ram-ddr5", name="DDR5 RAM 64GB", available=20, price=800),
            Product(sku="ssd-2tb", name="NVMe SSD 2TB", available=12, price=250),
            Product(sku="psu-1200w", name="Power Supply 1200W", available=8, price=300),
        ]

        # Shopping basket (sku -> quantity)
        self.basket: Dict[str, int] = {}

        # Race condition simulation
        self.simulate_race_condition = simulate_race_condition
        self.first_checkout_attempted = False

    def list_products(self, offset: int = 0, limit: int = 10) -> Dict:
        """
        List products with pagination.

        Args:
            offset: Starting index for pagination
            limit: Maximum number of products to return

        Returns:
            Dictionary with products, message, and next_offset
        """
        # Check for page limit exceeded (simulate API behavior from screenshot)
        if limit > 3:
            return {
                "message": f"page limit exceeded limit: 3",
                "code": "",
                "status_code": 400
            }

        # Get paginated products
        end_idx = offset + limit
        paginated_products = self.products[offset:end_idx]

        # Calculate next offset (-1 if no more products)
        next_offset = end_idx if end_idx < len(self.products) else -1

        return {
            "products": [p.model_dump() for p in paginated_products],
            "next_offset": next_offset
        }

    def add_to_basket(self, sku: str, amount: int) -> Dict:
        """
        Add product to basket.

        Args:
            sku: Product SKU
            amount: Quantity to add

        Returns:
            Dictionary with success status and message
        """
        # Check if product exists
        product = next((p for p in self.products if p.sku == sku), None)
        if not product:
            return {
                "message": f"Product {sku} not found",
                "code": "NOT_FOUND",
                "status_code": 404
            }

        # Add to basket
        if sku in self.basket:
            self.basket[sku] += amount
        else:
            self.basket[sku] = amount

        return {
            "message": "ok"
        }

    def view_basket(self) -> Dict:
        """
        View current basket contents.

        Returns:
            Dictionary with basket items
        """
        items = []
        for sku, quantity in self.basket.items():
            product = next((p for p in self.products if p.sku == sku), None)
            if product:
                items.append(
                    BasketItem(
                        sku=sku,
                        name=product.name,
                        quantity=quantity,
                        price=product.price
                    ).model_dump()
                )

        return {
            "items": items
        }

    def remove_from_basket(self, sku: str, amount: int) -> Dict:
        """
        Remove product from basket.

        Args:
            sku: Product SKU
            amount: Quantity to remove

        Returns:
            Dictionary with success status and message
        """
        if sku not in self.basket:
            return {
                "message": f"Product {sku} not in basket",
                "code": "NOT_FOUND",
                "status_code": 404
            }

        # Remove or decrease quantity
        self.basket[sku] -= amount
        if self.basket[sku] <= 0:
            del self.basket[sku]

        return {
            "message": "ok"
        }

    def checkout_basket(self) -> Dict:
        """
        Checkout basket (simulate inventory check).

        Simulates a race condition on first checkout attempt where inventory
        is reduced by another customer, causing the agent to adjust basket.

        Returns:
            Dictionary with checkout result
        """
        if not self.basket:
            return {
                "message": "Basket is empty",
                "code": "EMPTY_BASKET",
                "status_code": 400
            }

        # Simulate race condition: another customer bought some GPUs before us!
        if self.simulate_race_condition and not self.first_checkout_attempted:
            self.first_checkout_attempted = True

            # Reduce GPU inventory to simulate someone else buying them
            for product in self.products:
                if product.sku == "gpu-h100":
                    product.available = 1  # Someone bought 2 out of 3
                elif product.sku == "gpu-a100":
                    product.available = 3  # Someone bought 1 out of 4

        # Check inventory for each item
        for sku, quantity in self.basket.items():
            product = next((p for p in self.products if p.sku == sku), None)
            if product and quantity > product.available:
                # Simulate the error from the screenshot
                return {
                    "message": f"insufficient inventory for product {sku} during checkout: available {product.available}, in basket {quantity}",
                    "code": "",
                    "status_code": 400
                }

        # Checkout successful - clear basket and update inventory
        for sku, quantity in self.basket.items():
            product = next((p for p in self.products if p.sku == sku), None)
            if product:
                product.available -= quantity

        self.basket.clear()

        return {
            "message": "ok"
        }
