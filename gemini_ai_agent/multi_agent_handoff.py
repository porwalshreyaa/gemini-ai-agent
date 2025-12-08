# Sub-agent: When Agent A calls Agent B as a sub-agent, the responsibility of answering the user is completely transferred to Agent B. Agent A is effectively out of the loop. All subsequent user input will be answered by Agent B.

# Handoffs - the initial agent delegates the entire conversation to a specialist once it has identified the user's request

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.adk.tools.agent_tool import AgentTool
from pydantic import BaseModel, Field
from typing import Optional
import asyncio

load_dotenv()


def refund(customer_id, reason):
    with open('./refunds.txt', 'a', encoding="utf-8") as file:
        file.write(f"Refund for customer having ID {customer_id} for {reason}.\n")
        return {"refund_issued": True}

class RefundParamsSchema(BaseModel):
    customer_id: str = Field(..., description="Id of the customer")
    reason: str = Field(..., description="reason for refund")

def process_refund(customer_id, reason):
    f"""
    This tool processes the refund for the customers.
    Args: {RefundParamsSchema}

    """
    return refund(customer_id, reason)

refund_agent = Agent(
    name="refund_agent",
    model="gemini-2.5-flash",
    description="Handles refund related queries as the Refund agent for an internet broadband company.",
    instruction=(
        "You are an expert in issuing refunds to the customers. Talk to the user and help them with what they need."
    ),
    tools=[process_refund],
)




def fetch_available_plans():
    """
    Fetches the available Plans for internet.
    """
    return [
        { "plan_id": '1', "price_inr": '399', "speed": '30MB/s'},
        { "plan_id": '2', "price_inr": '999', "speed": '100MB/s'},
        { "plan_id": '3', "price_inr": '1499', "speed": '200MB/s'}
    ]


sales_agent = Agent(
    name="sales_agent",
    model="gemini-2.5-flash",
    description="Handles sales related queries as the Sales agent for an internet broadband company.",
    instruction=(
        "You are an expert sales agent for an internet broadband company. Talk to the user and help them with what they need."
    ),
    tools=[fetch_available_plans],
)





reception_agent = Agent(
    name="reception_agent",
    model="gemini-2.5-flash",
    description="""
    You have two agents available:
    - sales_agent: Expert in handeling queries like all plans and pricing available. Good for new customers
    - refund_agent: Expert in handeling user queries for existing customers and issue refunds and help them
    """,
    instruction=(
        "You are the customer facing agent expert in understanding what customer needs and then route them or handoff them to the right agent."
    ),
    sub_agents=[sales_agent, refund_agent]

)






async def main(query: str):
    runner = InMemoryRunner(agent=reception_agent)

    events = await runner.run_debug(query)

    for event in events:
        if not event.content or not event.content.parts:
            return
        for part in event.content.parts:
            if (
                part
                and part.function_response

            ):
                print(part.function_response)
                return


if __name__ == "__main__":
    asyncio.run(main("I am shifting to another location, I want refund for this plan and I'll like to buy a new plan. My customer Id is '786ohlp97gJ'"))