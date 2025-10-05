#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys
import os

# Add lib directory to path (it's in the same directory as this script)
libdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

import logging
from waveshare_epd import epd7in5h
import time
from PIL import Image, ImageDraw, ImageFont
import requests
from datetime import datetime

logging.basicConfig(level=logging.INFO)

# Configuration
LATITUDE = -33.8688  # Sydney coordinates (change to your location)
LONGITUDE = 151.2093
TIMEZONE = "Australia/Sydney"

def get_weather():
    """Fetch weather data from Open-Meteo API (no API key needed)"""
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={LATITUDE}&longitude={LONGITUDE}&current=temperature_2m,weather_code&timezone={TIMEZONE}"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        temp = data['current']['temperature_2m']
        weather_code = data['current']['weather_code']
        
        # Simple weather code mapping
        weather_desc = {
            0: "Clear sky",
            1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
            45: "Foggy", 48: "Foggy",
            51: "Light drizzle", 53: "Drizzle", 55: "Heavy drizzle",
            61: "Light rain", 63: "Rain", 65: "Heavy rain",
            71: "Light snow", 73: "Snow", 75: "Heavy snow",
            80: "Rain showers", 81: "Rain showers", 82: "Heavy rain showers",
            95: "Thunderstorm", 96: "Thunderstorm", 99: "Thunderstorm"
        }
        
        description = weather_desc.get(weather_code, "Unknown")
        return temp, description
    except Exception as e:
        logging.error(f"Error fetching weather: {e}")
        return None, "Unable to fetch"

def main():
    try:
        logging.info("Initializing e-Paper display...")
        epd = epd7in5h.EPD()
        epd.init()
        epd.Clear()
        
        # Create image
        logging.info("Creating display content...")
        image = Image.new('1', (epd.width, epd.height), 255)  # 255: white
        draw = ImageDraw.Draw(image)
        
        # Load fonts (try different sizes)
        try:
            font_large = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 80)
            font_medium = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 50)
            font_small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 35)
        except:
            logging.warning("TrueType fonts not found, using default")
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Get current date and time
        now = datetime.now()
        date_str = now.strftime("%A, %B %d, %Y")
        time_str = now.strftime("%I:%M %p")
        
        # Get weather
        temp, weather = get_weather()
        
        # Draw content
        y_offset = 80
        
        # Draw time (large)
        draw.text((50, y_offset), time_str, font=font_large, fill=0)
        y_offset += 120
        
        # Draw date
        draw.text((50, y_offset), date_str, font=font_medium, fill=0)
        y_offset += 100
        
        # Draw separator line
        draw.line((50, y_offset, epd.width - 50, y_offset), fill=0, width=3)
        y_offset += 50
        
        # Draw weather
        if temp is not None:
            weather_text = f"Temperature: {temp}°C"
            draw.text((50, y_offset), weather_text, font=font_medium, fill=0)
            y_offset += 80
            draw.text((50, y_offset), weather, font=font_small, fill=0)
        else:
            draw.text((50, y_offset), "Weather unavailable", font=font_small, fill=0)
        
        # Display image
        logging.info("Displaying on e-Paper...")
        epd.display(epd.getbuffer(image))
        
        logging.info("Going to sleep...")
        epd.sleep()
        
        logging.info("Done!")
        
    except Exception as e:
        logging.error(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
