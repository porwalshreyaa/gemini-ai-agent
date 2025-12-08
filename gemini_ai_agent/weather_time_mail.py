from timezonefinder import TimezoneFinder
from geopy.geocoders import Nominatim
import datetime
from zoneinfo import ZoneInfo
from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
import requests
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os
from pydantic import BaseModel, Field
from typing import Optional
import asyncio

load_dotenv()
sender_email = os.environ.get("SENDER_EMAIL")
sender_password = os.environ.get("SENDER_PASSWORD")


geolocator = Nominatim(user_agent="weather_time_agent")
tf = TimezoneFinder()

def get_weather(city: str) -> dict:
    """Retrieves the current weather report for a specified city.
    Args:
        city (str): The name of the city for which to retrieve the weather report.
    Returns:
        dict: status and result or error msg.
    """
    if not city:
        return {
            "status": "error",
            "error_message": f"Weather information for '{city}' is not available.",
        }
    try:    
        url = f"https://wttr.in/{city.lower()}?format=%C+%t"
        response = requests.get(url)
        if response.status_code != 200:
            return {
                "status": "error",
                "error_message": "Weather service unavailable."
            }

        report = response.text.strip()
        return {
            "status": "success",
            "report": (
                 f"Weather information for {city.title()}: {report}."
            ),
        }

    except Exception as e:
        return {"status": "error", "error_message": str(e)}

class GetWeatherResultSchema(BaseModel):
    city: str = Field(..., description="Name of the city")
    degree_c: float = Field(..., description="Temperature in Celsius")
    condition:  Optional[str] = Field(None, description="Weather condition")

def get_current_time(city: str) -> dict:
    """Returns the current time in a specified city.

    Args:
        city (str): The name of the city for which to retrieve the current time.

    Returns:
        dict: status and result or error msg.
    """
    if not city:
        return {
            "status": "error",
            "error_message": f"Time for '{city}' is not available.",
        }
    
    try:
        location = geolocator.geocode(city)
        if not location:
            return {"status": "error", "error_message": f"City '{city}' not found."}

        timezone_str = tf.timezone_at(lng=location.longitude, lat=location.latitude)
        if not timezone_str:
            return {"status": "error", "error_message": f"No timezone found for '{city}'."}

        tz = ZoneInfo(timezone_str)
        now = datetime.datetime.now(tz)

        return {
            "status": "success",
            "report": f"The current time in {city} is {now.strftime('%Y-%m-%d %H:%M:%S %Z %z')}."
        }

    except Exception as e:
        return {"status": 'error', "error_message": str(e)}

def send_email(email: str, subject: str, body: str) -> dict:
    """Sends an email.
    Args:
        email (str): email address to,
        subject (str): subject of the email,
        body (str): body of the email.
    Returns:
        dict: status and result or error msg.
    """
    if (not email):
        return {
            "status": "error",
            "error_message": f"Could not send email without email address",
        }
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = sender_email
        msg['To'] = email

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")


root_agent = Agent(
    name="weather_time_agent",
    model="gemini-2.5-flash-lite",
    description=(
        "Agent to answer questions about the time and weather in a city and send emails."
    ),
    instruction=(
        "You are a helpful agent who can answer user questions about the time and weather in a city. Return the final result in string format. You can send the time and weather details as email to a given email address if asked to."
    ),
    tools=[get_weather, get_current_time, send_email],
    output_schema= GetWeatherResultSchema,
)

async def main(query: str):
    runner = InMemoryRunner(agent=root_agent)

    events = await runner.run_debug(query)

    for event in events:
        # if event.type == "model_output":
        #     print(event.content)
        print(event)


if __name__ == "__main__":
    asyncio.run(main(f"Fetch weather and time of Surat and mail me at '{os.environ.get("MY_EMAIL")}'"))