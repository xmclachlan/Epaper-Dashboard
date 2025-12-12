import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- LOCATIONS ---
LATITUDE = -33.8688  # Sydney
LONGITUDE = 151.2093
TIMEZONE = "Australia/Sydney"

# --- WEATHER (OpenWeatherMap) ---
# Get API key: https://openweathermap.org/api
OWM_API_KEY = os.getenv("OWM_API_KEY", "")

# --- TRANSPORT (TfNSW) ---
# Get API key: https://opendata.transport.nsw.gov.au/
TFNSW_API_KEY = os.getenv("TFNSW_API_KEY", "")
BUS_STOP_ID = "206663" # Example: Central Station

# --- CALENDAR (ICS / iCAL) ---
# Google: Settings -> Secret Address in iCal format
# iCloud: Public Calendar -> Webcal URL (replace webcal:// with https://)
CALENDAR_URL = os.getenv("CALENDAR_URL", "")

# --- DISPLAY SETTINGS ---
# Set to True if you want to rotate the display 180 degrees
ROTATE_180 = False
