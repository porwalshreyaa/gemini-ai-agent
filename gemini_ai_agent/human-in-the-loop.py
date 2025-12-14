from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.tools import FunctionalTool
import asyncio

async def external_approval_tool(amount: float, reason: str) -> str:
    print("\n=== HUMAN APPROVAL REQUIRED ===")
    print(f"Amount: {amount}")
    print(f"Reason: {reason}")

    loop = asyncio.get_running_loop()

    while True:
        decision = await loop.run_in_executor(
            None,
            input,
            "Approve? (y/n): "
        )

        decision = decision.strip().lower()
        if decision in ("y", "yes"):
            return "approved"
        elif decision in ("n", "no"):
            return "rejected"

# This tool would:
# 1. Take details (e.g., request_id, amount, reason).
# 2. Send these details to a human review system (e.g., via API).
# 3. Poll or wait for the human response (approved/rejected).
# 4. Return the human's decision.
# async def external_approval_tool(amount: float, reason: str) -> str: ...

approval_tool = FunctionTool(func=external_approval_tool)

# agent prepares request
prepare_request = LlmAgent(
    name='PrepareApproval',
    instruction="Prepare the approval request details based on user input. Store amount and reason in state."
    # likely sets state['approval_amount'] and state['approval_reason']
)

# agent calls human approval tool
request_approval = LlmAgent(
    name="RequestHumanApproval",
    instruction="Use the external_approval_tool with amount from state['approval_amount] and reason from  state['approval_reason']",
    tools=[approval_tool],
    output_key='human_decision'
)

# agent that proceeds based on human decision
process_decision = LlmAgent(
    name='ProcessDecision',
    instruction="Check {human_decision}. If 'approved', proceed.If 'rejected', inform user."
)

approval_workflow = SequentialAgent(
    name="HumanApprovalWorkflow",
    sub_agents=[prepare_request, request_approval,process_decision]
)