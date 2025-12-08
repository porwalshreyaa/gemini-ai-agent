from gemini_ai_agent.agent import (
    get_weather,
    get_current_time,
    send_email
)
import pytest
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------
# TEST get_weather
# ---------------------------------------------------------

@patch("gemini_ai_agent.agent.requests.get")
def test_get_weather_success(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = "Sunny +25°C"
    mock_get.return_value = mock_resp

    result = get_weather("London")
    assert result["status"] == "success"
    assert "London" in result["report"]
    assert "Sunny" in result["report"]


def test_get_weather_empty_city():
    result = get_weather("")
    assert result["status"] == "error"


@patch("gemini_ai_agent.agent.requests.get")
def test_get_weather_service_unavailable(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 503
    mock_get.return_value = mock_resp

    result = get_weather("Paris")
    assert result["status"] == "error"
    assert "unavailable" in result["error_message"].lower()


# ---------------------------------------------------------
# TEST get_current_time
# ---------------------------------------------------------

@patch("gemini_ai_agent.agent.geolocator.geocode")
@patch("gemini_ai_agent.agent.tf.timezone_at")
@patch("gemini_ai_agent.agent.datetime.datetime")
def test_get_current_time_success(mock_datetime, mock_timezone_at, mock_geocode):
    # Mock geocode return
    mock_location = MagicMock()
    mock_location.longitude = 10
    mock_location.latitude = 20
    mock_geocode.return_value = mock_location

    # Mock timezone result
    mock_timezone_at.return_value = "Europe/Berlin"

    # Mock datetime
    mock_now = MagicMock()
    mock_now.strftime.return_value = "2024-01-01 12:00:00 CET +0100"
    mock_datetime.now.return_value = mock_now

    result = get_current_time("Berlin")
    assert result["status"] == "success"
    assert "Berlin" in result["report"]
    assert "2024" in result["report"]


def test_get_current_time_empty_city():
    result = get_current_time("")
    assert result["status"] == "error"


@patch("gemini_ai_agent.agent.geolocator.geocode", return_value=None)
def test_get_current_time_city_not_found(mock_geo):
    result = get_current_time("NowhereCity")
    assert result["status"] == "error"
    assert "not found" in result["error_message"].lower()


# ---------------------------------------------------------
# TEST send_email
# ---------------------------------------------------------

@patch("gemini_ai_agent.agent.smtplib.SMTP_SSL")
def test_send_email_success(mock_smtp):
    mock_server = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_server

    result = send_email("test@example.com", "Hello", "Body text")

    mock_server.login.assert_called_once()
    mock_server.send_message.assert_called_once()


def test_send_email_no_address():
    result = send_email("", "Hi", "Body")
    assert result["status"] == "error"
