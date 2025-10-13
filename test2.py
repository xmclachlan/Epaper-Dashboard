#!/usr/bin/env python3
"""
E-Paper Dashboard: Daily Weather, Calendar, and Australian Facts
Displays: Date, Weather Summary, Showers, Wind, Calendar Events, Random Facts
Designed for 800x480 pixel 4-color displays (e.g., Waveshare epd7in5h).
"""

import requests
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta
import random
import os
import sys
import logging
from typing import Dict, List, Tuple, Any
import json

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# --- Configuration & Setup ---
libdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

DISPLAY_WIDTH = 800
DISPLAY_HEIGHT = 480

# Define RGB Colors
RGB_WHITE = (255, 255, 255)
RGB_BLACK = (0, 0, 0)
RGB_RED   = (255, 0, 0)
RGB_YELLOW = (255, 255, 0)

# Your location (Sydney)
LATITUDE = -33.8688
LONGITUDE = 151.2093

# Google Calendar API Configuration
# Instructions: Create OAuth credentials at https://console.cloud.google.com
# Download credentials.json and run the script once to authorize
CALENDAR_ID = 'primary'  # Change to your calendar ID if needed
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

# --- Australian Facts Pool ---
AUSTRALIAN_FACTS = [
    "Australia is home to 21 of the world's 25 most venomous snakes.",
    "The Great Barrier Reef is the world's largest living structure, visible from space.",
    "Australia has over 10,000 beaches - you could visit one every day for 27 years.",
    "Melbourne has been ranked the world's most liveable city multiple times.",
    "Australians invented the black box flight recorder, WiFi technology, and Google Maps.",
    "Tasmania has the cleanest air in the world, comparable to Antarctica.",
    "The Australian Alps receive more snowfall than Switzerland each year.",
    "Australia is the only continent without an active volcano.",
    "Sydney's Opera House took 14 years to build and was completed 10 years late.",
    "Australia has the world's longest fence - the Dingo Fence is 5,614 km long.",
    "Koalas sleep up to 22 hours per day to conserve energy from their eucalyptus diet.",
    "Australia is home to 1,500 species of spiders, but only a few are dangerous.",
    "The Box Jellyfish, found in Australian waters, is the most venomous creature on Earth.",
    "Australians consume 1.35 million litres of beer per day.",
    "In 1880, Australia's wild rabbit population grew from 24 to 600 million in just 10 years.",
]

# --- Utility Functions: Data Fetching ---

def get_daily_weather() -> Dict[str, Any]:
    """Fetch detailed daily weather forecast from Open-Meteo."""
    default_weather = {
        'temp_max': '--', 'temp_min': '--', 'summary': 'Weather unavailable',
        'rain_probability': 0, 'rain_times': [], 'wind_speed': '--', 
        'wind_direction': '--', 'wind_times': []
    }
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            'latitude': LATITUDE,
            'longitude': LONGITUDE,
            'daily': 'temperature_2m_max,temperature_2m_min,precipitation_probability_max,weathercode',
            'hourly': 'precipitation_probability,windspeed_10m,winddirection_10m',
            'temperature_unit': 'celsius',
            'windspeed_unit': 'kmh',
            'timezone': 'auto',
            'forecast_days': 1
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        daily = data.get('daily', {})
        hourly = data.get('hourly', {})
        
        # Today's summary
        temp_max = round(daily.get('temperature_2m_max', [0])[0])
        temp_min = round(daily.get('temperature_2m_min', [0])[0])
        weather_code = daily.get('weathercode', [2])[0]
        
        # Weather summary
        weather_descriptions = {
            0: 'Clear', 1: 'Mainly Clear', 2: 'Partly Cloudy',
            3: 'Overcast', 45: 'Foggy', 48: 'Foggy',
            51: 'Drizzle', 61: 'Light Rain', 63: 'Rain',
            65: 'Heavy Rain', 71: 'Snow', 95: 'Thunderstorms'
        }
        summary = weather_descriptions.get(weather_code, 'Cloudy')
        
        # Find rain times
        rain_probs = hourly.get('precipitation_probability', [])
        times = hourly.get('time', [])
        rain_times = []
        
        for i, prob in enumerate(rain_probs[:24]):  # Next 24 hours
            if prob and prob > 50:  # Significant rain probability
                time_str = datetime.fromisoformat(times[i]).strftime('%I%p').lstrip('0')
                rain_times.append(time_str)
        
        # Find peak wind times
        wind_speeds = hourly.get('windspeed_10m', [])
        wind_directions = hourly.get('winddirection_10m', [])
        
        max_wind_speed = max(wind_speeds[:24]) if wind_speeds else 0
        max_wind_idx = wind_speeds.index(max_wind_speed) if wind_speeds else 0
        wind_dir_deg = wind_directions[max_wind_idx] if wind_directions else 0
        
        # Convert wind direction to compass
        wind_dir = get_wind_direction(wind_dir_deg)
        
        # Find strong wind times (>25 km/h)
        wind_times = []
        for i, speed in enumerate(wind_speeds[:24]):
            if speed and speed > 25:
                time_str = datetime.fromisoformat(times[i]).strftime('%I%p').lstrip('0')
                wind_times.append(time_str)
        
        return {
            'temp_max': temp_max,
            'temp_min': temp_min,
            'summary': summary,
            'rain_probability': daily.get('precipitation_probability_max', [0])[0],
            'rain_times': rain_times[:3],  # Limit to 3 times
            'wind_speed': round(max_wind_speed),
            'wind_direction': wind_dir,
            'wind_times': wind_times[:3]
        }
    except Exception as e:
        logging.error(f"Weather API error: {e}")
        return default_weather

def get_wind_direction(degrees: float) -> str:
    """Convert wind direction in degrees to compass direction."""
    directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                  'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    idx = round(degrees / 22.5) % 16
    return directions[idx]

def get_calendar_events() -> List[Dict[str, str]]:
    """Fetch today's calendar events from Google Calendar."""
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        import pickle
        
        creds = None
        # Token file stores user's access and refresh tokens
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        
        # If no valid credentials, let user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        
        service = build('calendar', 'v3', credentials=creds)
        
        # Get today's events
        now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = now + timedelta(days=1)
        
        events_result = service.events().list(
            calendarId=CALENDAR_ID,
            timeMin=now.isoformat() + 'Z',
            timeMax=end_of_day.isoformat() + 'Z',
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        formatted_events = []
        for event in events[:5]:  # Limit to 5 events
            start = event['start'].get('dateTime', event['start'].get('date'))
            
            # Parse time
            if 'T' in start:
                event_time = datetime.fromisoformat(start.replace('Z', '+00:00'))
                time_str = event_time.strftime('%I:%M%p').lstrip('0')
            else:
                time_str = 'All Day'
            
            formatted_events.append({
                'time': time_str,
                'title': event.get('summary', 'Untitled Event')
            })
        
        return formatted_events
        
    except ImportError:
        logging.warning("Google Calendar API not installed. Install: pip install google-auth-oauthlib google-api-python-client")
        return []
    except Exception as e:
        logging.error(f"Calendar API error: {e}")
        return []

def get_hourly_fact() -> str:
    """Get a random Australian fact that updates on the hour."""
    # Use current hour as seed for consistency within the hour
    now = datetime.now()
    seed = now.year * 10000 + now.month * 100 + now.day * 24 + now.hour
    random.seed(seed)
    fact = random.choice(AUSTRALIAN_FACTS)
    random.seed()  # Reset seed
    return fact

# --- Utility Functions: Drawing & Layout ---

def load_fonts() -> Dict[str, ImageFont.ImageFont]:
    """Load system fonts with fallbacks."""
    font_path = '/usr/share/fonts/truetype/dejavu/'
    try:
        fonts = {
            'title': ImageFont.truetype(f'{font_path}DejaVuSans-Bold.ttf', 48),
            'large': ImageFont.truetype(f'{font_path}DejaVuSans-Bold.ttf', 32),
            'medium': ImageFont.truetype(f'{font_path}DejaVuSans.ttf', 24),
            'small': ImageFont.truetype(f'{font_path}DejaVuSans.ttf', 18),
        }
    except IOError:
        logging.warning("Default fonts not found. Using PIL fallback fonts.")
        fonts = {k: ImageFont.load_default() for k in ['title', 'large', 'medium', 'small']}
    return fonts

def wrap_text(text: str, font: ImageFont.ImageFont, max_width: int, draw: ImageDraw.ImageDraw) -> List[str]:
    """Wraps text into lines that fit within max_width."""
    lines = []
    words = text.split()
    if not words:
        return []
    
    current_line = words[0]
    for word in words[1:]:
        test_line = current_line + ' ' + word
        if draw.textbbox((0, 0), test_line, font=font)[2] <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word
    lines.append(current_line)
    return lines

def create_dashboard() -> Image.Image:
    """Creates the dashboard layout."""
    image = Image.new('RGB', (DISPLAY_WIDTH, DISPLAY_HEIGHT), RGB_WHITE)
    draw = ImageDraw.Draw(image)
    fonts = load_fonts()
    
    now = datetime.now()
    weather = get_daily_weather()
    events = get_calendar_events()
    fact = get_hourly_fact()
    
    PADDING = 20
    y_pos = PADDING
    
    # --- Header: Date ---
    date_text = now.strftime('%A, %d %B %Y')
    draw.text((PADDING, y_pos), date_text, font=fonts['title'], fill=RGB_BLACK)
    y_pos += 60
    
    # --- Weather Section ---
    draw.text((PADDING, y_pos), "TODAY'S WEATHER", font=fonts['large'], fill=RGB_RED)
    y_pos += 45
    
    # Temperature range and summary
    weather_line1 = f"{weather['temp_min']}°C - {weather['temp_max']}°C  •  {weather['summary']}"
    draw.text((PADDING, y_pos), weather_line1, font=fonts['medium'], fill=RGB_BLACK)
    y_pos += 35
    
    # Showers expected
    if weather['rain_times']:
        rain_text = f"Showers likely: {', '.join(weather['rain_times'])}"
        draw.text((PADDING, y_pos), rain_text, font=fonts['medium'], fill=RGB_BLACK)
    else:
        draw.text((PADDING, y_pos), "No rain expected", font=fonts['medium'], fill=RGB_BLACK)
    y_pos += 35
    
    # Wind information
    wind_text = f"Wind: {weather['wind_speed']} km/h {weather['wind_direction']}"
    if weather['wind_times']:
        wind_text += f"  (Strong: {', '.join(weather['wind_times'])})"
    draw.text((PADDING, y_pos), wind_text, font=fonts['medium'], fill=RGB_BLACK)
    y_pos += 50
    
    # --- Calendar Section ---
    draw.text((PADDING, y_pos), "TODAY'S EVENTS", font=fonts['large'], fill=RGB_RED)
    y_pos += 45
    
    if events:
        for event in events:
            event_text = f"{event['time']}  •  {event['title']}"
            # Truncate if too long
            if draw.textbbox((0, 0), event_text, font=fonts['medium'])[2] > DISPLAY_WIDTH - 2 * PADDING:
                event_text = event_text[:60] + "..."
            draw.text((PADDING, y_pos), event_text, font=fonts['medium'], fill=RGB_BLACK)
            y_pos += 32
    else:
        draw.text((PADDING, y_pos), "No events scheduled", font=fonts['medium'], fill=RGB_BLACK)
        y_pos += 32
    
    y_pos += 20
    
    # --- Australian Fact Section ---
    draw.text((PADDING, y_pos), "DID YOU KNOW?", font=fonts['large'], fill=RGB_YELLOW)
    y_pos += 45
    
    # Wrap fact text
    fact_lines = wrap_text(fact, fonts['medium'], DISPLAY_WIDTH - 2 * PADDING, draw)
    for line in fact_lines[:3]:  # Limit to 3 lines
        draw.text((PADDING, y_pos), line, font=fonts['medium'], fill=RGB_BLACK)
        y_pos += 30
    
    # --- Footer ---
    footer_text = f"Updated: {now.strftime('%I:%M%p').lstrip('0')}"
    footer_bbox = draw.textbbox((0, 0), footer_text, font=fonts['small'])
    footer_y = DISPLAY_HEIGHT - footer_bbox[3] - 10
    draw.text((DISPLAY_WIDTH - footer_bbox[2] - PADDING, footer_y), 
              footer_text, font=fonts['small'], fill=RGB_BLACK)
    
    return image

# --- Main Execution ---

def update_display(image: Image.Image):
    """Update the e-paper display."""
    try:
        from waveshare_epd import epd7in5h as epd_module
        logging.info("Updating e-paper display...")
        
        epd = epd_module.EPD()
        epd.init()
        epd.Clear()
        
        buffer = epd.getbuffer(image)
        epd.display(buffer)
        
        epd.sleep()
        logging.info("Display updated and sleeping.")
        
    except ImportError:
        logging.error("E-paper driver not found. Ensure it is in the 'lib' directory.")
    except Exception as e:
        logging.error(f"E-paper display error: {e}")

def main():
    """Main execution function."""
    logging.info("Creating dashboard...")
    
    try:
        image = create_dashboard()
    except Exception as e:
        logging.error(f"Error creating dashboard: {e}")
        sys.exit(1)
    
    # Save preview
    preview_filename = 'dashboard_preview.png'
    image.save(preview_filename)
    logging.info(f"Preview saved to '{preview_filename}'.")
    
    # Update display
    update_display(image)
    logging.info("Script finished.")

if __name__ == '__main__':
    main()
