# Agent-as-a-Tool: When Agent A calls Agent B as a tool (using Agent-as-a-Tool), Agent B's answer is passed back to Agent A, which then summarizes the answer and generates a response to the user. Agent A retains control and continues to handle future user input.

# Manager (agent as tools) - a central agent owns the conversation and invokes specialized agents that are exposed as tools.

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
    description="Refund agent for an internet broadband company to help users with their queries.",
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
    description="Sales agent for an internet broadband company to help users with their queries.",
    instruction=(
        "You are an expert sales agent for an internet broadband company. Talk to the user and help them with what they need."
    ),
    tools=[fetch_available_plans, AgentTool(agent=refund_agent)],
)




async def main(query: str):
    runner = InMemoryRunner(agent=sales_agent)

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
    asyncio.run(main("I did not like your internet services, I want refund. My customer Id is '00yhkiu379G'"))