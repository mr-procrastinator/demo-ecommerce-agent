# Planning Agent Implementation Summary

This document summarizes the implementation of a dynamic planning agent system that mimics the behavior shown in the reference screenshot.

## Overview

The system implements a multi-step task execution framework using atomic agents, with:
- **5 E-commerce tools** for product management
- **Mock datastore** simulating a product catalog and shopping cart
- **Planning agent** with dynamic step-by-step execution
- **Error handling** and recovery strategies
- **Step logging** matching production AI agent behavior

## Architecture

```
orchestration_agent/
├── tools/
│   ├── ecommerce/
│   │   ├── datastore.py           # Mock product catalog & basket
│   │   ├── list_products.py       # Pagination-based product listing
│   │   ├── add_to_basket.py       # Add items to shopping cart
│   │   ├── view_basket.py         # View cart contents
│   │   ├── remove_from_basket.py  # Remove/adjust cart items
│   │   └── checkout_basket.py     # Complete purchase with validation
│   ├── calculator.py
│   └── searxng_search.py
├── orchestrator.py                 # Basic tool orchestrator
└── planning_agent.py              # Dynamic planning agent

gpu_race_demo.py                   # "Buy ALL GPUs" demo task
test_ecommerce_tools.py            # Tool validation tests
```

## Key Features

### 1. E-Commerce Tools

All tools follow the atomic agents pattern with:
- Pydantic input/output schemas
- BaseToolConfig configuration
- BaseTool implementation
- Shared datastore for state management

#### ListProductsTool
- **Pagination**: Returns max 3 items per page (configurable)
- **Error handling**: Returns 400 status code if limit exceeded
- **Parameters**: `offset` (int), `limit` (int)
- **Returns**: Product list, next_offset (-1 if no more)

#### AddToBasketTool
- **Validation**: Checks product exists before adding
- **Parameters**: `sku` (string), `amount` (int)
- **Returns**: Success/error message with status code

#### ViewBasketTool
- **No parameters**: Shows current basket state
- **Returns**: List of items with SKU, name, quantity, price

#### RemoveFromBasketTool
- **Auto-cleanup**: Removes item if quantity reaches 0
- **Parameters**: `sku` (string), `amount` (int)
- **Returns**: Success/error message

#### CheckoutBasketTool
- **Inventory validation**: Checks available stock before purchase
- **Error format**: Matches screenshot - "insufficient inventory for product {sku} during checkout: available {n}, in basket {m}"
- **Success behavior**: Clears basket, updates inventory
- **No parameters**: Uses current basket state

### 2. Mock Datastore

Simulates a real e-commerce backend with:
- **Product catalog**: 8 products including GPUs, CPUs, RAM, etc.
- **Inventory tracking**: Available quantities
- **Shopping basket**: In-memory dict (sku -> quantity)
- **Error simulation**: API limit errors, inventory errors

Product examples:
```python
Product(sku="gpu-h100", name="Nvidia H100", available=3, price=20000)
Product(sku="gpu-a100", name="Nvidia A100", available=4, price=11950)
```

### 3. Planning Agent

The core orchestration logic:

```python
class PlanningExecutor:
    def execute_task(self, task: str, max_steps: int = 20):
        # Planning loop
        while not goal_achieved and step_count < max_steps:
            # 1. Get next action from agent
            agent_output = planning_agent.run(input)

            # 2. Execute tool
            result = execute_tool(tool_call, tools...)

            # 3. Update context with result
            context += step_summary

            # 4. Log step in screenshot format
            print(f"Planning step_{N}... {reasoning}")
            print(f"  tool='{name}' {params}")
            print(f"  OUTPUT {result}")
```

**Features:**
- Dynamic step generation based on task
- Context accumulation across steps
- Error detection and recovery
- Goal achievement detection
- Step-by-step logging

### 4. Error Handling

The system handles multiple error scenarios:

1. **Page limit exceeded**:
   - Agent requests limit > 3 for list_products
   - Datastore returns: `{"message": "page limit exceeded", "status_code": 400}`
   - Agent adjusts and uses limit=3

2. **Insufficient inventory**:
   - Agent adds more items to basket than available
   - Checkout returns: `{"message": "insufficient inventory for product gpu-h100...", "status_code": 400}`
   - Agent removes excess from basket and retries

3. **Type conversion**:
   - Agent may pass wrong parameter types
   - `execute_tool()` converts to correct schema automatically

## Usage

### Running the GPU Race Demo

```bash
# Set OpenAI API key
export OPENAI_API_KEY='your-key-here'

# Run demo
poetry run python gpu_race_demo.py
```

**Expected output:**
```
Planning step_1... List all available products
  tool='list_products' offset=0 limit=3
  OUTPUT {"products":[...],"next_offset":3}

Planning step_2... Add Nvidia H100 GPUs to basket
  tool='add_to_basket' sku='gpu-h100' amount=3
  OUTPUT {"message":"ok"}

Planning step_3... Add Nvidia A100 GPUs to basket
  tool='add_to_basket' sku='gpu-a100' amount=4
  OUTPUT {"message":"ok"}

Planning step_4... Checkout with GPUs in basket
  tool='checkout_basket'
  OUTPUT {"message":"ok","status_code":200}
```

### Testing Individual Tools

```bash
poetry run python test_ecommerce_tools.py
```

Validates:
- Product listing with pagination
- Basket operations (add, view, remove)
- Checkout with inventory validation
- Error scenarios

## Comparison to Reference Screenshot

The implementation matches the screenshot behavior:

| Feature | Screenshot | Implementation |
|---------|-----------|----------------|
| Step numbering | `Planning step_1...` | ✅ |
| Tool logging | `tool='name' params` | ✅ |
| Output format | `OUTPUT {...}` | ✅ |
| Pagination | limit=3, next_offset | ✅ |
| Error messages | "insufficient inventory..." | ✅ |
| Error codes | status_code: 400 | ✅ |
| Basket adjustment | Remove excess items | ✅ |
| Checkout validation | Inventory check | ✅ |

## Extension Points

To add new e-commerce operations:

1. **Create tool file**: `orchestration_agent/tools/ecommerce/your_tool.py`
2. **Define schemas**: Input, Output, Config (extends BaseToolConfig)
3. **Implement BaseTool**: `run()` method calls datastore
4. **Add to datastore**: Implement backend logic in `datastore.py`
5. **Update planning agent**:
   - Add to Union type in `ToolCall.parameters`
   - Add to `execute_tool()` function
   - Update system prompt background

## Key Insights

1. **Shared Datastore Pattern**: All tools share a single datastore instance to maintain state consistency
2. **Union Type Handling**: The agent may return wrong parameter types for Union schemas - convert at execution time
3. **Empty Schema Tools**: Tools with no parameters (view_basket, checkout_basket) need special handling
4. **Context Accumulation**: Agent improves with each step by maintaining full history
5. **Logging Format**: Consistent format enables easy debugging and matches production patterns

## Files Reference

- `datastore.py:172` - EcommerceDatastore class
- `planning_agent.py:146` - execute_tool() with type conversion
- `planning_agent.py:197` - execute_task() planning loop
- `gpu_race_demo.py:43` - Demo execution
- `README.md` - Full documentation with examples
