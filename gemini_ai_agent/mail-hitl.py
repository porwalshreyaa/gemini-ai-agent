from timezonefinder import TimezoneFinder
from geopy.geocoders import Nominatim
import datetime
from zoneinfo import ZoneInfo
from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.adk.tools import FunctionTool
import requests
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os
import asyncio

# ===================== ENV =====================
load_dotenv()
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")
MY_EMAIL=os.environ.get("MY_EMAIL")

# ===================== GEO =====================
geolocator = Nominatim(user_agent="weather_time_agent")
tf = TimezoneFinder()

# ===================== TOOLS =====================
def get_weather(city: str) -> dict:
    url = f"https://wttr.in/{city}?format=%C+%t"
    r = requests.get(url)
    return {"weather": r.text.strip()}

def get_current_time(city: str) -> dict:
    location = geolocator.geocode(city)
    tz_str = tf.timezone_at(lng=location.longitude, lat=location.latitude)
    tz = ZoneInfo(tz_str)
    now = datetime.datetime.now(tz)
    return {"time": now.strftime("%Y-%m-%d %H:%M:%S %Z")}

async def human_approval_tool(to_email: str, subject: str, body: str) -> str:
    print("\n========== HUMAN APPROVAL REQUIRED ==========")
    print(f"TO: {to_email}")
    print(f"SUBJECT: {subject}")
    print("BODY:")
    print(body)
    print("============================================")

    loop = asyncio.get_running_loop()
    while True:
        decision = await loop.run_in_executor(
            None, input, "Approve email? (y/n): "
        )
        decision = decision.strip().lower()
        if decision in ("y", "yes"):
            return "approved"
        if decision in ("n", "no"):
            return "rejected"

def send_email(to_email: str, subject: str, body: str) -> dict:
    msg = MIMEText(body)
    msg["From"] = SENDER_EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)

    return {"status": "sent"}

approval_tool = FunctionTool(func=human_approval_tool)

# ===================== AGENT =====================
root_agent = Agent(
    name="weather_time_agent",
    model="gemini-2.5-flash-lite",
    description="Weather + time agent with mandatory human approval before emailing",
    instruction="""
RULES (MANDATORY):
- If the user asks to send an email, you MUST:
  1. Fetch weather
  2. Fetch time
  3. Construct email subject + body
  4. CALL human_approval_tool
  5. ONLY IF approval == 'approved', call send_email
  6. IF approval == 'rejected', stop and say email was not sent

DO NOT ask the user for confirmation in text.
DO NOT send email without calling approval tool.
""",
    tools=[
        get_weather,
        get_current_time,
        approval_tool,
        send_email,
    ],
)

# ===================== RUNNER =====================
async def main():
    runner = InMemoryRunner(agent=root_agent)

    query = f"Fetch weather and time of Surat and email it to {MY_EMAIL}"
    events = await runner.run_debug(query)

    for event in events:
        print(event)

if __name__ == "__main__":
    asyncio.run(main())
