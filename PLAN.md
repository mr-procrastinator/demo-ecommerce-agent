# E-Commerce AI Agent Implementation Plan

## Overview
Create an AI agent system that can autonomously shop for products (GPUs in the example) using atomic agents framework. The agent should handle product browsing, inventory management, basket operations, and checkout.

## Architecture

### 1. Core Agent Structure
```
orchestration_agent/
├── orchestrator.py          # Main orchestration logic
├── tools/
│   ├── product_catalog.py   # Product listing and search
│   ├── basket_manager.py    # Shopping cart operations
│   ├── inventory_checker.py # Stock availability verification
│   └── checkout_handler.py  # Purchase completion
└── schemas/
    ├── product_schemas.py   # Product data models
    └── order_schemas.py     # Order and basket models
```

## Detailed Tool Specifications

### Tool 1: Product Catalog Tool
**Purpose**: Browse and search available products with filtering

**Capabilities**:
- List products with pagination (offset, limit)
- Filter by category, price range, availability
- Search by product name or SKU
- Return structured product data

**Input Schema**:
```python
class ProductCatalogInput:
    action: str  # "list_all", "search", "filter"
    offset: int = 0
    limit: int = 10
    category: Optional[str]
    price_max: Optional[float]
    search_term: Optional[str]
    availability_filter: bool = True
```

**Output Schema**:
```python
class ProductCatalogOutput:
    products: List[Product]
    total_count: int
    next_offset: Optional[int]
    has_more: bool
```

**Product Model**:
```python
class Product:
    sku: str
    name: str
    price: float
    available_quantity: int
    category: str
    specifications: dict
```

---

### Tool 2: Basket Manager Tool
**Purpose**: Manage shopping cart operations

**Capabilities**:
- Add items with quantities
- Remove items
- Update quantities
- View current basket
- Clear basket

**Input Schema**:
```python
class BasketManagerInput:
    action: str  # "add", "remove", "view", "update", "clear"
    sku: Optional[str]
    quantity: Optional[int]
```

**Output Schema**:
```python
class BasketManagerOutput:
    status: str  # "success", "error"
    message: str
    basket_items: List[BasketItem]
    total_items: int
    total_value: float
```

**BasketItem Model**:
```python
class BasketItem:
    sku: str
    name: str
    quantity: int
    unit_price: float
    subtotal: float
```

---

### Tool 3: Inventory Checker Tool
**Purpose**: Verify product availability and stock levels

**Capabilities**:
- Check real-time inventory
- Validate basket against stock
- Reserve items temporarily
- Get restock notifications

**Input Schema**:
```python
class InventoryCheckerInput:
    action: str  # "check_single", "validate_basket", "reserve"
    sku: Optional[str]
    quantity: Optional[int]
    basket_items: Optional[List[dict]]
```

**Output Schema**:
```python
class InventoryCheckerOutput:
    status: str
    available: bool
    current_stock: int
    validation_errors: List[dict]
    reservation_id: Optional[str]
```

---

### Tool 4: Checkout Handler Tool
**Purpose**: Complete purchase transactions

**Capabilities**:
- Validate final basket
- Process payment simulation
- Generate order confirmation
- Handle checkout errors

**Input Schema**:
```python
class CheckoutHandlerInput:
    basket_items: List[dict]
    payment_method: str
    shipping_address: dict
    validate_only: bool = False
```

**Output Schema**:
```python
class CheckoutHandlerOutput:
    status: str  # "success", "failed", "validation_error"
    order_id: Optional[str]
    confirmation_message: str
    errors: List[str]
    total_amount: float
```

---

## Orchestrator Agent Design

### System Prompt Elements

**Background**:
- Expert shopping assistant specializing in electronics
- Capable of understanding product requirements
- Makes intelligent decisions about product selection
- Handles inventory constraints gracefully

**Capabilities**:
- Parse user shopping requests
- Search and filter products based on criteria
- Compare products and make recommendations
- Manage multi-step shopping workflows
- Handle errors and constraints (out of stock, budget limits)

**Decision Logic**:
1. Understand user intent and requirements
2. Search/list products matching criteria
3. Evaluate options based on availability and price
4. Add suitable items to basket
5. Verify inventory before checkout
6. Complete purchase

### Input/Output Schemas

**Orchestrator Input**:
```python
class ShoppingTaskInput:
    task_description: str  # "Buy ALL GPUs", "Find best GPU under $500"
    budget: Optional[float]
    preferences: dict  # brand, specifications, etc.
    environment_id: str  # unique shopping session
```

**Orchestrator Output**:
```python
class ShoppingTaskOutput:
    status: str
    steps_completed: List[str]
    items_purchased: List[dict]
    total_spent: float
    summary: str
```

---

## Implementation Steps

### Phase 1: Tool Development (Week 1)
1. Create ProductCatalogTool with mock data backend
2. Implement BasketManagerTool with in-memory storage
3. Build InventoryCheckerTool with simulated stock
4. Develop CheckoutHandlerTool with validation logic

### Phase 2: Data Layer (Week 1-2)
1. Create mock product database (JSON/SQLite)
2. Implement inventory tracking system
3. Add session management for baskets
4. Build order history storage

### Phase 3: Orchestrator Integration (Week 2)
1. Configure orchestrator agent with all tools
2. Implement tool selection logic
3. Add context providers (current basket state, budget tracking)
4. Create multi-step planning capability

### Phase 4: Error Handling (Week 2-3)
1. Handle out-of-stock scenarios
2. Manage budget constraints
3. Implement retry logic for API failures
4. Add validation at each step

### Phase 5: Testing & Refinement (Week 3)
1. Test individual tools
2. Test orchestrator workflows
3. Handle edge cases (empty inventory, budget exceeded)
4. Optimize prompt engineering for better decisions

---

## Key Features from the Image

### Multi-Step Planning
The agent demonstrates:
- **Step 1-3**: Paginated product listing
- **Step 4**: Adding items to basket
- **Step 5**: Adding more items (bulk operation)
- **Step 6**: Checkout attempt (insufficient inventory)
- **Step 7**: View basket to verify
- **Step 8**: Remove excess items
- **Step 9**: Retry checkout with updated quantities
- **Step 10**: Success confirmation

### Error Recovery
- Detects inventory shortfall during checkout
- Automatically adjusts quantities
- Retries operation with corrected data

### State Management
- Maintains basket state across operations
- Tracks what's been added/removed
- Validates before each critical operation

---

## Context Providers Needed

### 1. Basket State Provider
```python
class BasketStateProvider(BaseDynamicContextProvider):
    """Tracks current basket contents"""
    def get_info(self) -> str:
        return f"Current basket: {items_count} items, ${total_value}"
```

### 2. Budget Tracker Provider
```python
class BudgetTrackerProvider(BaseDynamicContextProvider):
    """Monitors spending against budget"""
    def get_info(self) -> str:
        return f"Budget: ${remaining} remaining of ${total}"
```

### 3. Task Progress Provider
```python
class TaskProgressProvider(BaseDynamicContextProvider):
    """Tracks completion status"""
    def get_info(self) -> str:
        return f"Steps completed: {steps}. Current goal: {current_goal}"
```

---

## Mock Data Structure

### Sample Products Database
```json
{
  "products": [
    {
      "sku": "gpu-h100",
      "name": "Nvidia H100",
      "price": 20000,
      "available": 3,
      "category": "gpu",
      "specs": {"memory": "80GB", "architecture": "Hopper"}
    },
    {
      "sku": "gpu-a100",
      "name": "Nvidia A100",
      "price": 11950,
      "available": 4,
      "category": "gpu",
      "specs": {"memory": "40GB", "architecture": "Ampere"}
    }
  ]
}
```

---

## Testing Scenarios

1. **Basic Purchase**: "Buy 2 Nvidia H100 GPUs"
2. **Budget Constraint**: "Buy GPUs under $50,000 total"
3. **Inventory Issue**: "Buy ALL GPUs" (handles stock limits)
4. **Multi-Product**: "Buy 5 A100s and 3 H100s"
5. **Search & Select**: "Find the cheapest GPU with 40GB+ memory"

---

## Expected Behavior

The agent should:
1. ✅ Parse complex user requests
2. ✅ Break down into atomic operations
3. ✅ Execute tools in logical sequence
4. ✅ Handle errors gracefully with retries
5. ✅ Maintain state across operations
6. ✅ Provide clear summaries of actions taken
7. ✅ Validate data at each critical step
8. ✅ Optimize for user intent (e.g., "ALL" means maximum available)

---

## Next Steps

1. Review this plan and confirm approach
2. Create tool implementations starting with ProductCatalogTool
3. Build mock data layer
4. Implement orchestrator with enhanced planning
5. Test with scenarios from the image
6. Iterate based on results

