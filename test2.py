#!/usr/bin/env python3
"""
E-Paper Dashboard: Unified 4-Color UI (Black, White, Red, Yellow)
Displays: Large Clock, Weather, Random Facts, and System Status.
Designed for 800x480 pixel 4-color displays (e.g., Waveshare epd2in15g).

NOTE: This script assumes the epd2in15g.py driver file is present in the 'lib' directory
and correctly handles 800x480 resolution and 4-color conversion.
"""

import requests
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import random
import os
import sys
import logging
from typing import Dict, List, Tuple, Any

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# --- Configuration & Setup ---
libdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

DISPLAY_WIDTH = 800
DISPLAY_HEIGHT = 480

# Define RGB Colors for Drawing (must match colors supported by the driver's palette)
RGB_WHITE = (255, 255, 255)
RGB_BLACK = (0, 0, 0)
RGB_RED   = (255, 0, 0)
RGB_YELLOW = (255, 255, 0)

# Your location coordinates
LATITUDE = -33.8688
LONGITUDE = 151.2093

# WMO Weather Code Mapping (Icon Condition, Description)
WEATHER_CODES: Dict[int, Tuple[str, str]] = {
    0: ('Sun', 'Clear sky'), 1: ('Sun', 'Mainly clear'), 2: ('Cloud', 'Partly cloudy'),
    3: ('Cloud', 'Overcast'), 45: ('Fog', 'Foggy'), 48: ('Fog', 'Rime fog'),
    51: ('Rain', 'Light drizzle'), 61: ('Rain', 'Light rain'), 63: ('Rain', 'Moderate rain'), 
    71: ('Snow', 'Light snow'), 95: ('Storm', 'Thunderstorm'),
}

# --- Utility Functions: Data Fetching ---

def get_weather() -> Dict[str, Any]:
    """Fetch current weather from Open-Meteo."""
    default_weather = {'temp': '--', 'condition': 'Cloud', 'description': 'Weather unavailable'}
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            'latitude': LATITUDE, 'longitude': LONGITUDE, 
            'current_weather': 'true', 'temperature_unit': 'celsius', 
            'timezone': 'auto'
        }
        response = requests.get(url, params=params, timeout=8)
        response.raise_for_status()
        data = response.json()
        current = data.get('current_weather', {})
        weather_code = current.get('weathercode', 2)
        
        icon_condition, description = WEATHER_CODES.get(weather_code, ('Cloud', 'Unknown condition'))

        return {
            'temp': round(current.get('temperature', 0)),
            'condition': icon_condition,
            'description': description
        }
    except requests.exceptions.RequestException as e:
        logging.error(f"Weather API error: {e}")
        return default_weather

def get_random_fact() -> str:
    """Fetch a random fact, with a useful fallback."""
    fallback_facts = [
        "E-Paper displays use microcapsules containing charged white and black particles suspended in a clear fluid.",
        "Yellow is often used on displays to indicate warnings or highlights.",
        "Your E-Paper display retains its image without drawing any power.",
        "The fastest recorded wind speed on Earth was 253 mph during Cyclone Olivia in 1996.",
    ]
    try:
        response = requests.get('https://uselessfacts.jsph.pl/api/v2/facts/random', timeout=8)
        response.raise_for_status()
        data = response.json()
        return data.get('text', random.choice(fallback_facts))
    except requests.exceptions.RequestException as e:
        logging.warning(f"Fact API error, using fallback: {e}")
        return random.choice(fallback_facts)

# --- Utility Functions: Drawing & Layout ---

def load_fonts() -> Dict[str, ImageFont.ImageFont]:
    """Load system fonts, with fallbacks."""
    font_path = '/usr/share/fonts/truetype/dejavu/'
    try:
        fonts = {
            'clock': ImageFont.truetype(f'{font_path}DejaVuSans-Bold.ttf', 120),
            'xl':    ImageFont.truetype(f'{font_path}DejaVuSans-Bold.ttf', 64),
            'l_bold': ImageFont.truetype(f'{font_path}DejaVuSans-Bold.ttf', 36),
            'm':     ImageFont.truetype(f'{font_path}DejaVuSans.ttf', 24),
            's':     ImageFont.truetype(f'{font_path}DejaVuSans.ttf', 18),
        }
    except IOError:
        logging.warning("Default fonts not found. Using PIL fallback fonts.")
        fonts = {k: ImageFont.load_default() for k in ['clock', 'xl', 'l_bold', 'm', 's']}
    return fonts

def wrap_text(text: str, font: ImageFont.ImageFont, max_width: int, draw: ImageDraw.ImageDraw) -> List[str]:
    """Wraps text into a list of lines that fit within max_width."""
    lines: List[str] = []
    words = text.split()
    if not words: return []
    current_line = words[0]
    
    for word in words[1:]:
        test_line = current_line + ' ' + word
        # Using draw to measure size
        if draw.textbbox((0, 0), test_line, font=font)[2] <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word
            
    lines.append(current_line)
    return lines

def draw_weather_icon(draw: ImageDraw.ImageDraw, condition: str, x: int, y: int, size: int, color: Tuple[int, int, int]):
    """Draws a simple weather icon on the canvas."""
    cx, cy = x + size // 2, y + size // 2
    r_sun = size // 3
    r_cloud = size // 3

    if condition == 'Sun':
        # Simple yellow/red sun
        draw.ellipse((cx - r_sun, cy - r_sun, cx + r_sun, cy + r_sun), fill=RGB_YELLOW, outline=RGB_RED, width=2)
    elif condition == 'Cloud' or condition == 'Fog':
        # Black cloud
        draw.ellipse((x, cy - r_cloud, x + r_cloud * 1.5, cy + r_cloud), fill=color)
        draw.ellipse((x + r_cloud * 0.5, cy - r_cloud * 1.5, x + r_cloud * 2.5, cy + r_cloud * 0.5), fill=color)
    elif condition == 'Rain':
        # Black cloud with red drops
        draw_weather_icon(draw, 'Cloud', x, y, size, RGB_BLACK)
        for i in range(4):
            dx = x + (i * size) // 5 + size // 8
            draw.line([(dx, cy + r_cloud + 5), (dx, cy + r_cloud + 20)], fill=RGB_RED, width=2)
    elif condition == 'Snow':
        # Black cloud with yellow snow
        draw_weather_icon(draw, 'Cloud', x, y, size, RGB_BLACK)
        for i in range(5):
            dx = x + (i * size) // 4 + size // 8
            draw.text((dx, cy + r_cloud + 5), '*', font=load_fonts()['m'], fill=RGB_YELLOW)
    elif condition == 'Storm':
        # Black cloud with yellow lightning
        draw_weather_icon(draw, 'Cloud', x, y, size, RGB_BLACK)
        
        # Draw lightning bolt (Yellow)
        draw.polygon([
            (cx - 10, cy + 10), (cx + 5, cy + 10), 
            (cx - 5, cy + 30), (cx + 10, cy + 30)
        ], fill=RGB_YELLOW)


def create_dashboard() -> Image.Image:
    """Creates the asymmetrical layout onto a single RGB image."""
    # Create single RGB image canvas
    image = Image.new('RGB', (DISPLAY_WIDTH, DISPLAY_HEIGHT), RGB_WHITE)
    draw = ImageDraw.Draw(image)
    
    fonts = load_fonts()
    now = datetime.now()
    weather = get_weather()
    fact = get_random_fact()
    
    # Define Layout Dimensions
    PADDING = 25
    TOP_BAR_HEIGHT = 60
    MAIN_PANEL_WIDTH = 550
    SIDEBAR_X_START = MAIN_PANEL_WIDTH + 1
    
    # --- 1. Draw Structure and Top Bar ---
    # Top bar background (Red)
    draw.rectangle([(0, 0), (DISPLAY_WIDTH, TOP_BAR_HEIGHT)], fill=RGB_RED)
    
    # Draw Date (White) - Left aligned
    date_text = now.strftime('%A, %d %B %Y')
    draw.text((PADDING, 15), date_text, font=fonts['l_bold'], fill=RGB_WHITE)

    # --- 2. Main Panel (Left) ---
    y_pos = TOP_BAR_HEIGHT + PADDING
    
    # Large Clock (Black text, Red AM/PM)
    time_text = now.strftime('%I:%M')
    am_pm_text = now.strftime('%p')
    
    # Center the time slightly
    time_bbox = draw.textbbox((0, 0), time_text, font=fonts['clock'])
    time_w = time_bbox[2] - time_bbox[0]
    time_x = (MAIN_PANEL_WIDTH - time_w) // 2 - 30 # Shift slightly left for AM/PM
    
    draw.text((time_x, y_pos), time_text, font=fonts['clock'], fill=RGB_BLACK)
    
    # Draw AM/PM (Red)
    am_pm_y = y_pos + 60
    draw.text((time_x + time_w + 10, am_pm_y), am_pm_text, font=fonts['l_bold'], fill=RGB_RED)
    
    y_pos += time_bbox[3] + PADDING
    
    # --- 3. Sidebar: Weather (Right) ---
    x_pos = SIDEBAR_X_START + PADDING
    # Start y_pos higher since "Current Weather" title is removed
    y_pos_weather = TOP_BAR_HEIGHT + PADDING 
    
    # Temperature (Yellow)
    temp_text = f"{weather['temp']}°C"
    draw.text((x_pos, y_pos_weather), temp_text, font=fonts['xl'], fill=RGB_RED)
    
    # Weather Description (Black)
    temp_text_height = fonts['xl'].getbbox(temp_text)[3]
    y_pos_weather += temp_text_height + 5 # Move Y past the temperature
    draw.text((x_pos, y_pos_weather), weather['description'], font=fonts['m'], fill=RGB_BLACK)
    
    # Weather Icon (Red/Yellow/Black)
    desc_text_height = fonts['m'].getbbox(weather['description'])[3]
    y_pos_weather += desc_text_height + 15 # Move Y past the description + spacing

    icon_size = 90
    # Now draw the icon starting below the description text
    draw_weather_icon(draw, weather['condition'], x_pos + 10, y_pos_weather, icon_size, RGB_BLACK)


    # --- 4. Fact Footer (Bottom Panel) ---
    y_pos_fact = 300
    
    # Header (Red)
    draw.text((PADDING, y_pos_fact), "FACT OF THE DAY", font=fonts['l_bold'], fill=RGB_RED)
    y_pos_fact += fonts['l_bold'].getbbox("FACT OF THE DAY")[3] + 10
    
    # Fact Content (Black)
    fact_lines = wrap_text(fact, fonts['m'], DISPLAY_WIDTH - 2 * PADDING, draw)
    
    for line in fact_lines[:4]: # Limit to 4 lines
        draw.text((PADDING, y_pos_fact), line, font=fonts['m'], fill=RGB_BLACK)
        y_pos_fact += fonts['m'].getbbox(line)[3] + 5

    # --- 5. Footer Status ---
    footer_text = f"Data fetched @ {now.strftime('%H:%M:%S')}"
    footer_y = DISPLAY_HEIGHT - fonts['s'].getbbox(footer_text)[3] - 5
    
    draw.text((DISPLAY_WIDTH - 250, footer_y), footer_text, font=fonts['s'], fill=RGB_BLACK)

    return image

# --- Main Execution ---

def update_display(image: Image.Image):
    """
    Update the e-paper display (epd2in15g) using the single-buffer method.
    The driver's getbuffer() handles the 4-color conversion.
    """
    try:
        # Import the correct module name based on the driver file
        from waveshare_epd import epd7in5h as epd_module 
        logging.info("Updating e-paper display...")
        
        epd = epd_module.EPD()
        epd.init()
        epd.Clear()
        
        # Get the single, packed buffer from the RGB image
        single_buffer = epd.getbuffer(image)
        
        # Use the corrected call method for epd2in15g (takes one buffer)
        epd.display(single_buffer) 
        
        epd.sleep()
        logging.info("Display updated and sleeping.")
        
    except ImportError:
        logging.error("E-paper driver not found (epd2in15g). Ensure it is in the 'lib' directory.")
    except Exception as e:
        # Log the specific error for debugging
        logging.error(f"E-paper display error: {e}")

def main():
    """Main execution function."""
    logging.info("Creating dashboard...")
    
    try:
        # Create the single combined RGB image
        image = create_dashboard()
    except Exception as e:
        logging.error(f"Error creating dashboard: {e}")
        sys.exit(1)
    
    # Save a preview of the RGB image
    preview_filename = 'dashboard_preview.png'
    image.save(preview_filename) 
    logging.info(f"Preview saved to '{preview_filename}'.")
    
    # Update the physical display (passing the single image)
    update_display(image)

    logging.info("Script finished.")

if __name__ == '__main__':
    main()
