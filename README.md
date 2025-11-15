# Orchestration Agent Example

This example demonstrates how to create Orchestrator Agents that intelligently decide between tools and execute complex multi-step tasks.

## Features
- **Basic Orchestration**: Intelligent tool selection between search and calculator tools
- **Dynamic Planning Agent**: Multi-step task execution with error handling and replanning
- **E-commerce Tools**: Complete shopping workflow (list, add to basket, checkout)
- **Mock Datastore**: In-memory product catalog and shopping basket
- **Dynamic input/output schema handling**
- **Real-time date context provider**
- **Rich console output formatting**
- **Step-by-step logging** similar to production AI agents

## Getting Started

1. Clone the Atomic Agents repository:
   ```bash
   git clone https://github.com/BrainBlend-AI/atomic-agents
   ```

2. Navigate to the orchestration-agent directory:
   ```bash
   cd atomic-agents/atomic-examples/orchestration-agent
   ```

3. Install dependencies using Poetry:
   ```bash
   poetry install
   ```

4. Set up environment variables:
   Create a `.env` file in the `orchestration-agent` directory with:
   ```env
   OPENAI_API_KEY=your_openai_api_key
   ```

5. Install SearXNG (See: https://github.com/searxng/searxng)

6. Run the basic orchestrator example:
   ```bash
   poetry run python orchestration_agent/orchestrator.py
   ```

7. Run the GPU Race demo (Planning Agent):
   ```bash
   poetry run python gpu_race_demo.py
   ```

## Components

### Input/Output Schemas

- **OrchestratorInputSchema**: Handles user input messages
- **OrchestratorOutputSchema**: Specifies tool selection and parameters
- **FinalAnswerSchema**: Formats the final response

### Tools

#### Basic Orchestrator Tools
These tools were installed using the Atomic Assembler CLI (See the main README [here](../../README.md) for more info)
The agent orchestrates between two tools:
- **SearXNG Search Tool**: For queries requiring factual information
- **Calculator Tool**: For mathematical calculations

#### E-commerce Tools (Planning Agent)
Five atomic tools for e-commerce operations:
- **ListProductsTool**: Lists available products with pagination support
  - Handles page limits (max 3 items per page)
  - Returns next_offset for pagination
- **AddToBasketTool**: Adds products to shopping basket
  - Parameters: sku, amount
- **ViewBasketTool**: Views current basket contents
  - Returns list of items with quantities and prices
- **RemoveFromBasketTool**: Removes products from basket
  - Parameters: sku, amount
- **CheckoutBasketTool**: Completes purchase with inventory validation
  - Returns errors if insufficient inventory

### Context Providers

- **CurrentDateProvider**: Provides the current date in YYYY-MM-DD format

## GPU Race Demo

The `gpu_race_demo.py` script demonstrates a complex multi-step task execution:

**Task**: "Buy ALL GPUs"

The planning agent will:
1. List all products (handling pagination with limit=3)
2. Identify GPU products from the catalog
3. Add GPUs to the basket
4. Attempt checkout
5. Handle inventory errors (if basket quantity > available)
6. Adjust basket quantities based on available inventory
7. Retry checkout until successful

**Example Output**:
```
Planning step_1... List all available GPU products
  tool='list_products' offset=0 limit=3
  OUTPUT {"products":[...],"next_offset":3}

Planning step_2... Continue listing products with next offset
  tool='list_products' offset=3 limit=3
  OUTPUT {"products":[...],"next_offset":-1}

Planning step_3... Add Nvidia H100 GPUs to basket
  tool='add_to_basket' sku='gpu-h100' amount=3
  OUTPUT {"message":"ok"}

...

Planning step_6... Checkout with GPUs in basket
  tool='checkout_basket'
  OUTPUT {"message":"insufficient inventory for product gpu-h100...","status_code":400}

Planning step_7... Adjust basket to match available inventory
  tool='remove_from_basket' sku='gpu-h100' amount=1
  OUTPUT {"message":"ok"}

Planning step_8... Retry checkout
  tool='checkout_basket'
  OUTPUT {"message":"ok","status_code":200}
```

This mimics real-world AI agent behavior with dynamic planning, error handling, and recovery strategies.
