#!/usr/bin/env python3
"""
Simple E-Paper Dashboard - 3x2 Grid
Displays: Date, Time, Weather, Random Facts
"""

import requests
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import random
import os
import sys

# Add lib directory to path (it's in the same directory as this script)
libdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

# Configuration
DISPLAY_WIDTH = 800
DISPLAY_HEIGHT = 480

# Your location coordinates (find at: https://www.latlong.net/)
LATITUDE = -33.8688   # Sydney
LONGITUDE = 151.2093  # Sydney

def get_weather():
    """Fetch current weather - NO API KEY NEEDED!"""
    try:
        # Option 1: Open-Meteo (completely free, no key needed)
        # Get coordinates for Sydney (replace with your location)
        lat, lon = -33.8688, 151.2093  # Sydney coordinates
        
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            'latitude': lat,
            'longitude': lon,
            'current_weather': 'true',
            'temperature_unit': 'celsius'
        }
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        current = data['current_weather']
        
        # Map WMO weather codes to descriptions
        wmo_codes = {
            0: 'Clear sky', 1: 'Mainly clear', 2: 'Partly cloudy', 3: 'Overcast',
            45: 'Foggy', 48: 'Foggy', 51: 'Light drizzle', 53: 'Drizzle',
            55: 'Heavy drizzle', 61: 'Light rain', 63: 'Rain', 65: 'Heavy rain',
            71: 'Light snow', 73: 'Snow', 75: 'Heavy snow', 95: 'Thunderstorm'
        }
        
        weather_code = current['weathercode']
        description = wmo_codes.get(weather_code, 'Unknown')
        
        return {
            'temp': round(current['temperature']),
            'condition': description.split()[0],  # First word
            'description': description
        }
    except Exception as e:
        print(f"Weather error: {e}")
        return {'temp': '--', 'condition': 'N/A', 'description': 'unavailable'}

def get_random_fact():
    """Fetch random fact from API"""
    try:
        response = requests.get('https://uselessfacts.jsph.pl/api/v2/facts/random', timeout=10)
        data = response.json()
        return data['text']
    except Exception as e:
        print(f"Fact error: {e}")
        # Fallback facts
        facts = [
            "Honey never spoils. Archaeologists have found 3000-year-old honey that's still edible.",
            "Octopuses have three hearts and blue blood.",
            "A day on Venus is longer than its year.",
            "Bananas are berries, but strawberries aren't.",
            "The Eiffel Tower can be 15 cm taller during summer.",
        ]
        return random.choice(facts)

def wrap_text(text, font, max_width, draw):
    """Wrap text to fit within max_width"""
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        current_line.append(word)
        test_line = ' '.join(current_line)
        bbox = draw.textbbox((0, 0), test_line, font=font)
        line_width = bbox[2] - bbox[0]
        
        if line_width > max_width:
            if len(current_line) == 1:
                lines.append(current_line[0])
                current_line = []
            else:
                current_line.pop()
                lines.append(' '.join(current_line))
                current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines

def create_dashboard():
    """Create the dashboard image"""
    # Create blank white image
    image = Image.new('1', (DISPLAY_WIDTH, DISPLAY_HEIGHT), 255)
    draw = ImageDraw.Draw(image)
    
    # Load fonts
    try:
        font_large = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 48)
        font_medium = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 32)
        font_small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 18)
        font_tiny = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 14)
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
        font_tiny = ImageFont.load_default()
    
    # Grid layout (3 columns x 2 rows)
    cell_width = DISPLAY_WIDTH // 3
    cell_height = DISPLAY_HEIGHT // 2
    padding = 20
    
    # Get data
    now = datetime.now()
    weather = get_weather()
    fact = get_random_fact()
    
    # Draw grid lines
    draw.line([(cell_width, 0), (cell_width, DISPLAY_HEIGHT)], fill=0, width=2)
    draw.line([(cell_width * 2, 0), (cell_width * 2, DISPLAY_HEIGHT)], fill=0, width=2)
    draw.line([(0, cell_height), (DISPLAY_WIDTH, cell_height)], fill=0, width=2)
    
    # ROW 1, COL 1: Date
    x = padding
    y = padding
    date_text = now.strftime('%A')
    draw.text((x, y), date_text, font=font_medium, fill=0)
    y += 40
    date_text2 = now.strftime('%B %d')
    draw.text((x, y), date_text2, font=font_medium, fill=0)
    y += 40
    date_text3 = now.strftime('%Y')
    draw.text((x, y), date_text3, font=font_small, fill=0)
    
    # ROW 1, COL 2: Time
    x = cell_width + padding
    y = padding + 20
    time_text = now.strftime('%I:%M')
    draw.text((x, y), time_text, font=font_large, fill=0)
    y += 60
    ampm = now.strftime('%p')
    draw.text((x, y), ampm, font=font_medium, fill=0)
    
    # ROW 1, COL 3: Weather
    x = cell_width * 2 + padding
    y = padding
    draw.text((x, y), "WEATHER", font=font_small, fill=0)
    y += 30
    temp_text = f"{weather['temp']}°C"
    draw.text((x, y), temp_text, font=font_large, fill=0)
    y += 60
    draw.text((x, y), weather['condition'], font=font_small, fill=0)
    y += 25
    # Wrap description
    desc_lines = wrap_text(weather['description'], font_tiny, cell_width - 2*padding, draw)
    for line in desc_lines[:2]:
        draw.text((x, y), line, font=font_tiny, fill=0)
        y += 18
    
    # ROW 2, COL 1-3: Random Fact (spanning full width)
    x = padding
    y = cell_height + padding
    draw.text((x, y), "RANDOM FACT", font=font_medium, fill=0)
    y += 40
    
    # Wrap fact text
    fact_lines = wrap_text(fact, font_small, DISPLAY_WIDTH - 2*padding, draw)
    for line in fact_lines[:8]:  # Max 8 lines
        draw.text((x, y), line, font=font_small, fill=0)
        y += 24
    
    return image

def update_display(image):
    """Update the e-paper display"""
    try:
        # Uncomment and adjust for your specific display model
        from waveshare_epd import epd7in5h
        epd = epd7in5h.EPD()
        epd.init()
        epd.Clear()
        epd.display(epd.getbuffer(image))
        epd.sleep()
    except Exception as e:
        print(f"Display error: {e}")

def main():
    """Main function"""
    print("Creating dashboard...")
    
    # Create dashboard image
    image = create_dashboard()
    
    # Save preview
    image.save('/home/pi/epaper-dash/dashboard_preview.png')
    print("Preview saved to dashboard_preview.png")
    
    # Update display
    update_display(image)
    
    print("Done!")

if __name__ == '__main__':
    main()
