"""Planning agent that dynamically plans and executes tasks using e-commerce tools."""
import os
from typing import Union, Optional, List
import openai
from pydantic import Field
from atomic_agents import AtomicAgent, AgentConfig, BaseIOSchema
from atomic_agents.context import SystemPromptGenerator
from cerebras.cloud.sdk import Cerebras

import instructor

import logging
import json

#Set up logging
# logging.basicConfig(
#     level=logging.DEBUG,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     handlers=[
#         logging.FileHandler('instructor_requests.log'),
#         logging.StreamHandler()  # Also print to console
#     ]
# )

# Enable instructor's internal logging
# logging.getLogger("instructor").setLevel(logging.DEBUG)
# logging.getLogger("openai").setLevel(logging.DEBUG)

# Import e-commerce tools
from orchestration_agent.tools.ecommerce import (
    EcommerceDatastore,
    ListProductsTool,
    ListProductsToolConfig,
    ListProductsToolInputSchema,
    ListProductsToolOutputSchema,
    AddToBasketTool,
    AddToBasketToolConfig,
    AddToBasketToolInputSchema,
    AddToBasketToolOutputSchema,
    ViewBasketTool,
    ViewBasketToolConfig,
    ViewBasketToolInputSchema,
    ViewBasketToolOutputSchema,
    RemoveFromBasketTool,
    RemoveFromBasketToolConfig,
    RemoveFromBasketToolInputSchema,
    RemoveFromBasketToolOutputSchema,
    CheckoutBasketTool,
    CheckoutBasketToolConfig,
    CheckoutBasketToolInputSchema,
    CheckoutBasketToolOutputSchema,
)


########################
# INPUT/OUTPUT SCHEMAS #
########################
class PlanningAgentInputSchema(BaseIOSchema):
    """Input schema for the Planning Agent."""

    task: str = Field(..., description="The high-level task to accomplish (e.g., 'Buy ALL GPUs')")
    context: str = Field("", description="Current context including history of actions and results")


class ToolCall(BaseIOSchema):
    """Schema for a tool call decision."""

    tool_name: str = Field(
        ...,
        description="Name of the tool to use: 'list_products', 'add_to_basket', 'view_basket', 'remove_from_basket', or 'checkout_basket'"
    )
    reasoning: str = Field(..., description="Reasoning for this step")
    parameters: Union[
        ListProductsToolInputSchema,
        AddToBasketToolInputSchema,
        ViewBasketToolInputSchema,
        RemoveFromBasketToolInputSchema,
        CheckoutBasketToolInputSchema,
    ] = Field(
        ...,
        description="Parameters for the tool. Use ViewBasketToolInputSchema for view_basket, CheckoutBasketToolInputSchema for checkout_basket (both have no parameters)."
    )


class PlanningAgentOutputSchema(BaseIOSchema):
    """Output schema for the Planning Agent."""

    tool_call: ToolCall = Field(..., description="The next tool to call")
    goal_achieved: bool = Field(False, description="Whether the goal has been achieved")


class GoalEvaluationInputSchema(BaseIOSchema):
    """Input schema for the Goal Evaluation Agent."""

    task: str = Field(..., description="The original task that was requested")
    execution_history: str = Field(..., description="Full history of steps taken and their results")
    last_result: str = Field(..., description="The result of the most recent tool execution")


class GoalEvaluationOutputSchema(BaseIOSchema):
    """Output schema for the Goal Evaluation Agent."""

    goal_achieved: bool = Field(..., description="Whether the task goal has been fully achieved")
    reasoning: str = Field(..., description="Explanation of why the goal is or isn't achieved")


class ContextSummarizerInputSchema(BaseIOSchema):
    """Input schema for the Context Summarizer Agent."""

    task: str = Field(..., description="The original task being executed")
    execution_history: str = Field(..., description="Full execution history of recent steps")
    step_count: int = Field(..., description="Current step number")


class ContextSummarizerOutputSchema(BaseIOSchema):
    """Output schema for the Context Summarizer Agent."""

    summary: str = Field(..., description="Concise summary of what has been accomplished in earlier steps (before the last 3)")
    key_facts: List[str] = Field(..., description="List of important facts to remember (e.g., identified products, basket state, incomplete operations)")
    current_state: str = Field(..., description="Description of the current state and what still needs to be done")

from openai import OpenAI as OpenRouterClient
client = instructor.from_openai(openai.OpenAI())
model="gpt-5"
model_api_parameters = {
}

# api_key = os.getenv("OPENROUTER_API_KEY")
# client = instructor.from_openai(OpenRouterClient(base_url="https://openrouter.ai/api/v1", api_key=api_key), mode= instructor.Mode.JSON)
# model = "google/gemini-2.5-flash"
# model_api_parameters = {
# }

# client = instructor.from_cerebras(Cerebras(api_key=os.getenv("CEREBRAS_API_KEY")), mode=instructor.Mode.CEREBRAS_TOOLS)
# model = "gpt-oss-120b"
# model_api_parameters = {
# }
#######################
# AGENT CONFIGURATION #
#######################
planning_agent_config = AgentConfig(
    client=client,
    model=model, #"gpt-5"
    model_api_parameters=model_api_parameters,
    system_prompt_generator=SystemPromptGenerator(
        background=[
            "You are a Planning Agent that executes e-commerce tasks by selecting and using the appropriate tools.",
            "You have access to the following tools:",
            "1. list_products: Lists available products with pagination",
            "   - Required parameters: offset (int), limit (int, max: 10)",
            "   - Returns: products list, next_offset",
            "   - NOTE: Use small page sizes (limit <= 10) to avoid API errors",
            "2. add_to_basket: Adds a product to the shopping basket",
            "   - Required parameters: sku (string), amount (int)",
            "   - Returns: success message",
            "3. view_basket: Views current basket contents",
            "   - Required parameters: NONE",
            "   - Returns: list of items in basket",
            "4. remove_from_basket: Removes products from basket",
            "   - Required parameters: sku (string), amount (int)",
            "   - Returns: success message",
            "5. checkout_basket: Completes the purchase (validates inventory)",
            "   - Required parameters: NONE",
            "   - Returns: success or error with details",
            "",
            "You execute tasks step-by-step, selecting one tool at a time.",
            "After each tool execution, you receive the result and plan the next step.",
            "You handle errors by adjusting your plan (e.g., if inventory is insufficient, adjust basket quantities).",
        ],
        steps=[
            "Analyze the current task and context (including previous actions and results)",
            "Determine the next logical step to accomplish the goal",
            "Select the appropriate tool and provide the required parameters",
            "Provide clear reasoning for your decision",
            "Set goal_achieved=True only when the task is fully completed",
        ],
        output_instructions=[
            "Select ONE tool to call for the next step",
            "Provide the tool name exactly as listed: 'list_products', 'add_to_basket', 'view_basket', 'remove_from_basket', or 'checkout_basket'",
            "Fill in the appropriate parameters for the selected tool",
            "Explain your reasoning for this step",
            "Set goal_achieved=True only after successful checkout or when the task cannot be completed",
        ],
    ),
)

planning_agent = AtomicAgent[PlanningAgentInputSchema, PlanningAgentOutputSchema](config=planning_agent_config)

# Goal Evaluation Agent Configuration
goal_evaluator_config = AgentConfig(
    client=instructor.from_openai(openai.OpenAI()),
    model="gpt-5-mini",
    system_prompt_generator=SystemPromptGenerator(
        background=[
            "You are a Goal Evaluation Agent that determines whether a task has been successfully completed.",
            "You analyze the execution history and the most recent result to make this determination.",
            "You are independent from the planning agent and provide an objective evaluation.",
        ],
        steps=[
            "Review the original task that was requested",
            "Analyze the full execution history including all steps taken",
            "Examine the most recent result to understand the current state",
            "Determine if the task goal has been fully achieved based on the evidence",
            "Provide clear reasoning for your decision",
        ],
        output_instructions=[
            "Set goal_achieved=True ONLY if the task has been completely accomplished",
            "For e-commerce tasks: goal is achieved when checkout returns success (status_code=200, message='ok')",
            "If checkout failed, basket is empty without success, or task is incomplete, set goal_achieved=False",
            "Provide specific reasoning citing evidence from the execution history",
            "Be strict: partial completion is NOT goal achievement",
        ],
    ),
)

goal_evaluator_agent = AtomicAgent[GoalEvaluationInputSchema, GoalEvaluationOutputSchema](config=goal_evaluator_config)

# # Context Summarizer Agent Configuration
# context_summarizer_config = AgentConfig(
#     client=instructor.from_openai(openai.OpenAI()),
#     model="gpt-5-mini",  # Use mini for cost efficiency
#     system_prompt_generator=SystemPromptGenerator(
#         background=[
#             "You are a Context Summarizer Agent that creates concise summaries of execution history.",
#             "Your role is to compress OLDER steps (before the last 3) into compact summaries.",
#             "The last 3 steps will be kept verbatim - you only summarize what came before.",
#             "You preserve critical information while reducing token usage.",
#         ],
#         steps=[
#             "Review the task and execution history (focusing on steps before the last 3)",
#             "Identify key accomplishments and state changes from earlier steps",
#             "Extract critical facts: products found, basket contents, errors, incomplete operations",
#             "Note what was INCOMPLETE (e.g., pagination not finished, not all products listed)",
#             "Describe the current state after all steps",
#         ],
#         output_instructions=[
#             "Summary: 2-4 sentences about what happened in EARLIER steps (before last 3)",
#             "Key facts: Critical information to remember",
#             "  - Products identified (with SKUs)",
#             "  - Items in basket (what and how many)",
#             "  - Incomplete operations (e.g., 'Only listed first 2 products, more remain at offset=2')",
#             "  - Errors encountered and resolved",
#             "  - Inventory issues",
#             "Current state: What is the state NOW and what still needs to be done",
#             "BE SPECIFIC about incomplete pagination and partial results",
#         ],
#     ),
# )

#context_summarizer_agent = AtomicAgent[ContextSummarizerInputSchema, ContextSummarizerOutputSchema](config=context_summarizer_config)


######################
# TOOL EXECUTION #
######################
def execute_tool(
    tool_call: ToolCall,
    list_products_tool: ListProductsTool,
    add_to_basket_tool: AddToBasketTool,
    view_basket_tool: ViewBasketTool,
    remove_from_basket_tool: RemoveFromBasketTool,
    checkout_basket_tool: CheckoutBasketTool,
) -> Union[
    ListProductsToolOutputSchema,
    AddToBasketToolOutputSchema,
    ViewBasketToolOutputSchema,
    RemoveFromBasketToolOutputSchema,
    CheckoutBasketToolOutputSchema,
]:
    """Execute the selected tool with the given parameters."""

    tool_name = tool_call.tool_name.strip() if tool_call.tool_name else ""
    params = tool_call.parameters

    # If tool_name is empty, try to infer from parameter type
    if not tool_name:
        if isinstance(params, ListProductsToolInputSchema):
            tool_name = "list_products"
        elif isinstance(params, AddToBasketToolInputSchema):
            tool_name = "add_to_basket"
        elif isinstance(params, ViewBasketToolInputSchema):
            tool_name = "view_basket"
        elif isinstance(params, RemoveFromBasketToolInputSchema):
            tool_name = "remove_from_basket"
        elif isinstance(params, CheckoutBasketToolInputSchema):
            tool_name = "checkout_basket"
        else:
            raise ValueError(f"Cannot infer tool from params type: {type(params)}")

    if tool_name == "list_products":
        if not isinstance(params, ListProductsToolInputSchema):
            params = ListProductsToolInputSchema(**params.model_dump())
        return list_products_tool.run(params)
    elif tool_name == "add_to_basket":
        if not isinstance(params, AddToBasketToolInputSchema):
            params = AddToBasketToolInputSchema(**params.model_dump())
        return add_to_basket_tool.run(params)
    elif tool_name == "view_basket":
        if not isinstance(params, ViewBasketToolInputSchema):
            params = ViewBasketToolInputSchema()
        return view_basket_tool.run(params)
    elif tool_name == "remove_from_basket":
        if not isinstance(params, RemoveFromBasketToolInputSchema):
            params = RemoveFromBasketToolInputSchema(**params.model_dump())
        return remove_from_basket_tool.run(params)
    elif tool_name == "checkout_basket":
        if not isinstance(params, CheckoutBasketToolInputSchema):
            params = CheckoutBasketToolInputSchema()
        return checkout_basket_tool.run(params)
    else:
        raise ValueError(f"Unknown tool: '{tool_name}', params type: {type(params)}")


######################
# PLANNING EXECUTOR #
######################
class PlanningExecutor:
    """Executes a high-level task using the planning agent and e-commerce tools."""

    def __init__(self, datastore: Optional[EcommerceDatastore] = None):
        """
        Initialize the planning executor.

        Args:
            datastore: Shared datastore for all tools (optional, creates new if not provided)
        """
        self.datastore = datastore or EcommerceDatastore()

        # Initialize all tools with shared datastore
        self.list_products_tool = ListProductsTool(datastore=self.datastore)
        self.add_to_basket_tool = AddToBasketTool(datastore=self.datastore)
        self.view_basket_tool = ViewBasketTool(datastore=self.datastore)
        self.remove_from_basket_tool = RemoveFromBasketTool(datastore=self.datastore)
        self.checkout_basket_tool = CheckoutBasketTool(datastore=self.datastore)

        self.step_count = 0
        self.context_history: List[str] = []
        self.full_history: List[str] = []  # Keep full history for reference
        self.context_summary: str = ""  # Current summarized context

    def _format_params(self, params: BaseIOSchema) -> str:
        """Format parameters for logging."""
        params_dict = params.model_dump()
        if not params_dict:  # Empty dict for tools with no params
            return ""
        return " ".join([f"{k}={v}" for k, v in params_dict.items()])

    def _format_output(self, output: BaseIOSchema) -> str:
        """Format output for logging."""
        output_dict = output.model_dump()
        # Format similar to screenshot
        formatted_parts = []
        for k, v in output_dict.items():
            if isinstance(v, list):
                formatted_parts.append(f'"{k}":{v}')
            elif isinstance(v, str):
                formatted_parts.append(f'"{k}":"{v}"')
            else:
                formatted_parts.append(f'"{k}":{v}')
        return "{" + ",".join(formatted_parts) + "}"

    def execute_task(self, task: str, max_steps: int = 20) -> dict:
        """
        Execute a high-level task.

        Args:
            task: The task to execute (e.g., "Buy ALL GPUs")
            max_steps: Maximum number of steps to prevent infinite loops

        Returns:
            Dictionary with execution summary
        """
        print(f"\n[Task] {task}")
        print("=" * 80)

        context = ""
        goal_achieved = False

        while not goal_achieved and self.step_count < max_steps:
            self.step_count += 1

            # Get next action from planning agent
            agent_input = PlanningAgentInputSchema(task=task, context=context)
            agent_output = planning_agent.run(agent_input)
            print(f"\n[Planning Agent Output] {agent_output.model_dump_json(indent=2)}")
            tool_call = agent_output.tool_call

            if(agent_output.goal_achieved):
                goal_achieved = True
                print(f"\n  ✓ Planning Agent indicates goal achieved.")
                break
            # Log the planning step
            print(f"\nPlanning step_{self.step_count}... {tool_call.reasoning}")
            print(f"  tool='{tool_call.tool_name}' {self._format_params(tool_call.parameters)}")

            # Execute the tool
            result = execute_tool(
                tool_call,
                self.list_products_tool,
                self.add_to_basket_tool,
                self.view_basket_tool,
                self.remove_from_basket_tool,
                self.checkout_basket_tool,
            )

            # Log the output
            print(f"  OUTPUT {self._format_output(result)}")

            # Update context with the result
            step_summary = f"Step {self.step_count}: {tool_call.reasoning}\n"
            step_summary += f"Tool: {tool_call.tool_name} with params {self._format_params(tool_call.parameters)}\n"
            step_summary += f"Result: {self._format_output(result)}\n"

            self.context_history.append(step_summary)
            self.full_history.append(step_summary)

            # Every 3 steps, summarize the context to keep it compact
            # if self.step_count % 3 == 0 and self.step_count > 3:
            #     print(f"\n  [Context Summarizer] Compressing history (step {self.step_count})...")

            #     # Get all history for summarization
            #     all_history = "\n".join(self.full_history)

            #     summarizer_input = ContextSummarizerInputSchema(
            #         task=task,
            #         execution_history=all_history,
            #         step_count=self.step_count
            #     )
            #     summary_result = context_summarizer_agent.run(summarizer_input)

            #     # Build compact context from summary + last 3 steps verbatim
            #     self.context_summary = f"=== Summary of earlier steps (1-{self.step_count - 3}) ===\n"
            #     self.context_summary += f"{summary_result.summary}\n\n"
            #     self.context_summary += "Key Facts:\n"
            #     for fact in summary_result.key_facts:
            #         self.context_summary += f"  • {fact}\n"
            #     self.context_summary += f"\nCurrent State: {summary_result.current_state}\n"
            #     self.context_summary += "\n=== Last 3 steps (full details) ===\n"

            #     # Keep last 3 steps with full reasoning
            #     last_three_steps = self.full_history[-3:]
            #     for i, step in enumerate(last_three_steps, start=self.step_count - 2):
            #         self.context_summary += f"\n{step}"

            #     # Replace verbose history with summary + last 3 steps
            #     self.context_history = [self.context_summary]

            #     old_size = len(all_history)
            #     new_size = len(self.context_summary)
            #     print(f"  [Context Summarizer] Compressed {old_size} chars to {new_size} chars ({100 - int(new_size/old_size*100)}% reduction)")
            #     print(f"  [Context Summarizer] Kept last 3 steps verbatim with full reasoning")

            # Build context for next iteration (either summary or recent steps)
            context = "\n".join(self.context_history)

            # Use goal evaluator agent to determine if task is complete (if not already set by planning agent)
            # if not goal_achieved:
            #     evaluator_input = GoalEvaluationInputSchema(
            #         task=task,
            #         execution_history=context,
            #         last_result=self._format_output(result)
            #     )
            #     evaluation = goal_evaluator_agent.run(evaluator_input)
            #     goal_achieved = evaluation.goal_achieved

            #     # Log evaluation reasoning
            #     print(f"\n  [Goal Evaluator] {evaluation.reasoning}")
            #     if goal_achieved:
            #         print(f"  [Goal Evaluator] ✓ Task completed!")
            #     else:
            #         print(f"  [Goal Evaluator] → Continuing...")


        print("\n" + "=" * 80)
        if goal_achieved:
            print(f"Task completed in {self.step_count} steps!")
        else:
            print(f"Max steps ({max_steps}) reached.")

        return {
            "steps": self.step_count,
            "goal_achieved": goal_achieved,
            "context": self.context_history,
            "full_history": self.full_history,
            "final_summary": self.context_summary,
        }


#################
# EXAMPLE USAGE #
#################
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv()

    # Create executor
    executor = PlanningExecutor()

    # Execute the task from the screenshot
    result = executor.execute_task("Buy ALL GPUs")

    print("\n\nSummary:")
    print(f"- Steps executed: {result['steps']}")
    print(f"- Goal achieved: {result['goal_achieved']}")
