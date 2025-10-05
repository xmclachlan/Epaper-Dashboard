#!/usr/bin/env python3
"""
Simple E-Paper Dashboard - Header, Footer, and 3 Columns
Displays: Date/Time, Weather, Random Facts, System Stats
"""

import requests
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import random
import os
import sys

# --- Configuration & Setup ---
# Add lib directory to path (it's in the same directory as this script)
libdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

# Display Configuration (Assuming a typical 800x480 resolution)
DISPLAY_WIDTH = 800
DISPLAY_HEIGHT = 480
# Colors for 3-color e-paper (0=Black, 255=White, Red/Other=Custom Value, typically Black is 0 and Red is 1)
# We will use two images for a 3-color display: one for Black/White and one for Red.
COLOR_BLACK = 0
COLOR_WHITE = 255
COLOR_RED = 1 # Used for the red mask image

# Your location coordinates (Sydney remains the default)
LATITUDE = -33.8688
LONGITUDE = 151.2093

# Global storage for system stats
LAST_RUN_TIME = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
# NOTE: Next run time is hard to predict accurately in a standalone script.
# We'll set a placeholder or use the time this script started running.
NEXT_RUN_TIME_PLACEHOLDER = "Scheduled via cron" 

# --- Utility Functions ---

def get_weather():
    """Fetch current weather - NO API KEY KEY NEEDED!"""
    try:
        lat, lon = LATITUDE, LONGITUDE
        
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            'latitude': lat,
            'longitude': lon,
            'current_weather': 'true',
            'temperature_unit': 'celsius',
            'timezone': 'auto' # Get accurate local time for weather
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
            'condition': description.split()[0],
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
        # Check if the line is empty (start of new line)
        test_line = ' '.join(current_line + [word])
        
        # PIL textbbox gives (left, top, right, bottom)
        # Calculate width of the text
        bbox = draw.textbbox((0, 0), test_line, font=font)
        line_width = bbox[2] - bbox[0]
        
        if line_width > max_width and current_line:
            # Word makes line too long, finish current line, start new one with the word
            lines.append(' '.join(current_line))
            current_line = [word]
        elif line_width > max_width and not current_line:
             # A single word is too long, just add it (will exceed bounds, but avoids infinite loop)
            lines.append(word)
            current_line = []
        else:
            # Word fits, add to current line
            current_line.append(word)
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines

def load_fonts():
    """Load standard and custom fonts"""
    # Prefer system fonts for thickness and clarity
    try:
        # Default fonts for a Linux system (like Raspberry Pi OS)
        font_xl = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 72) # TIME
        font_large = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 40) # HEADER/DATE/TEMP
        font_medium = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 24) # SECTION TITLES
        font_small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 18) # FACT/FOOTER
        font_tiny = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 16) # Smaller details
    except:
        # Fallback for systems without these specific fonts
        print("Warning: Custom fonts not found. Using default fonts.")
        font_xl = ImageFont.load_default()
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
        font_tiny = ImageFont.load_default()
        
    return {
        'xl': font_xl, 'large': font_large, 'medium': font_medium, 
        'small': font_small, 'tiny': font_tiny
    }

def draw_text_box(draw, x, y, width, lines, font, fill=COLOR_BLACK, max_lines=None, line_spacing=4):
    """Helper to draw wrapped text in a box"""
    if max_lines:
        lines = lines[:max_lines]
    
    current_y = y
    for line in lines:
        draw.text((x, current_y), line, font=font, fill=fill)
        # Calculate line height based on font size and spacing
        bbox = draw.textbbox((0, 0), line, font=font)
        line_height = bbox[3] - bbox[1]
        current_y += line_height + line_spacing
    return current_y

# --- Main Dashboard Creation ---

def create_dashboard():
    """Create the dashboard images (black/white and red) for a 3-color display"""
    # Create blank white images (mode '1' for black/white, then use a custom value for red mask)
    black_image = Image.new('1', (DISPLAY_WIDTH, DISPLAY_HEIGHT), COLOR_WHITE)
    red_image = Image.new('1', (DISPLAY_WIDTH, DISPLAY_HEIGHT), COLOR_WHITE)
    
    # Draw contexts
    draw_black = ImageDraw.Draw(black_image)
    draw_red = ImageDraw.Draw(red_image)
    
    # Load fonts
    fonts = load_fonts()
    
    # Define Layout Dimensions
    HEADER_HEIGHT = 60
    FOOTER_HEIGHT = 45
    MAIN_HEIGHT = DISPLAY_HEIGHT - HEADER_HEIGHT - FOOTER_HEIGHT
    COLUMN_WIDTH = DISPLAY_WIDTH // 3
    
    PADDING = 15
    
    # Get data
    now = datetime.now()
    weather = get_weather()
    fact = get_random_fact()
    
    # --- 1. Draw Grid Lines ---
    
    # Separator below header (red line for emphasis)
    draw_red.line([(0, HEADER_HEIGHT), (DISPLAY_WIDTH, HEADER_HEIGHT)], fill=COLOR_RED, width=3)
    # Separator above footer (black line)
    draw_black.line([(0, DISPLAY_HEIGHT - FOOTER_HEIGHT), (DISPLAY_WIDTH, DISPLAY_HEIGHT - FOOTER_HEIGHT)], fill=COLOR_BLACK, width=2)
    # Column lines (black)
    draw_black.line([(COLUMN_WIDTH, HEADER_HEIGHT), (COLUMN_WIDTH, DISPLAY_HEIGHT - FOOTER_HEIGHT)], fill=COLOR_BLACK, width=2)
    draw_black.line([(COLUMN_WIDTH * 2, HEADER_HEIGHT), (COLUMN_WIDTH * 2, DISPLAY_HEIGHT - FOOTER_HEIGHT)], fill=COLOR_BLACK, width=2)
    
    # --- 2. Draw Header ---
    
    header_text = "Xavier's Display Dashboard"
    # Center the header text in the red section, using a large font
    header_bbox = draw_red.textbbox((0, 0), header_text, font=fonts['large'])
    header_width = header_bbox[2] - header_bbox[0]
    x_header = (DISPLAY_WIDTH - header_width) // 2
    y_header = (HEADER_HEIGHT - (header_bbox[3] - header_bbox[1])) // 2 # Vertical center
    draw_red.text((x_header, y_header), header_text, font=fonts['large'], fill=COLOR_RED)
    
    # --- 3. Draw Main Columns ---
    
    # --- COL 1: Date & Time (Black for date, Red for Time) ---
    x1_start = PADDING
    y1_start = HEADER_HEIGHT + PADDING
    col_width = COLUMN_WIDTH - 2*PADDING
    
    # Date (Day of Week, Month Day)
    date_text1 = now.strftime('%A, %B %d')
    draw_black.text((x1_start, y1_start), date_text1, font=fonts['medium'], fill=COLOR_BLACK)
    
    # Year
    y1_start += 30 # Move down
    date_text2 = now.strftime('%Y')
    draw_black.text((x1_start, y1_start), date_text2, font=fonts['medium'], fill=COLOR_BLACK)

    # Time (Large Red Text)
    y1_start += 50 
    time_text = now.strftime('%I:%M')
    # Center time text in column for better look
    time_bbox = draw_red.textbbox((0, 0), time_text, font=fonts['xl'])
    time_width = time_bbox[2] - time_bbox[0]
    x_time = COLUMN_WIDTH // 2 - time_width // 2
    draw_red.text((x_time, y1_start), time_text, font=fonts['xl'], fill=COLOR_RED)
    
    # AM/PM
    y1_start += 75 
    ampm = now.strftime('%p')
    ampm_bbox = draw_red.textbbox((0, 0), ampm, font=fonts['large'])
    ampm_width = ampm_bbox[2] - ampm_bbox[0]
    x_ampm = COLUMN_WIDTH // 2 - ampm_width // 2
    draw_red.text((x_ampm, y1_start), ampm, font=fonts['large'], fill=COLOR_RED)
    
    # --- COL 2: Weather (Red for Temp, Black for condition) ---
    x2_start = COLUMN_WIDTH + PADDING
    y2_start = HEADER_HEIGHT + PADDING
    
    draw_black.text((x2_start, y2_start), "WEATHER", font=fonts['medium'], fill=COLOR_BLACK)
    
    # Temperature (Large Red Text)
    y2_start += 40
    temp_text = f"{weather['temp']}°C"
    draw_red.text((x2_start, y2_start), temp_text, font=fonts['xl'], fill=COLOR_RED)
    
    # Main Condition (Black Text)
    y2_start += 75
    draw_black.text((x2_start, y2_start), weather['condition'].upper(), font=fonts['large'], fill=COLOR_BLACK)
    
    # Detailed Description (Small Black Wrapped Text)
    y2_start += 50
    col_width_center = COLUMN_WIDTH - 2*PADDING
    desc_lines = wrap_text(weather['description'], fonts['small'], col_width_center, draw_black)
    draw_text_box(draw_black, x2_start, y2_start, col_width_center, desc_lines, fonts['small'], fill=COLOR_BLACK, max_lines=4, line_spacing=2)

    # --- COL 3: Random Fact (Black Title, Red Text) ---
    x3_start = COLUMN_WIDTH * 2 + PADDING
    y3_start = HEADER_HEIGHT + PADDING
    
    draw_black.text((x3_start, y3_start), "RANDOM FACT", font=fonts['medium'], fill=COLOR_BLACK)
    
    # Fact Text (Small Red Wrapped Text)
    y3_start += 40
    col_width_center = COLUMN_WIDTH - 2*PADDING
    fact_lines = wrap_text(fact, fonts['small'], col_width_center, draw_red)
    draw_text_box(draw_red, x3_start, y3_start, col_width_center, fact_lines, fonts['small'], fill=COLOR_RED, max_lines=7, line_spacing=4)
    
    # --- 4. Draw Footer ---
    
    # System Stats (Tiny Black Text)
    y_footer = DISPLAY_HEIGHT - FOOTER_HEIGHT + PADDING
    
    # Last Run Time
    stat1 = f"Last Run: {LAST_RUN_TIME}"
    draw_black.text((PADDING, y_footer), stat1, font=fonts['tiny'], fill=COLOR_BLACK)
    
    # Next Run Time (Placeholder)
    stat2 = f"Next Run: {NEXT_RUN_TIME_PLACEHOLDER}"
    # Center text in middle of footer
    stat2_bbox = draw_black.textbbox((0, 0), stat2, font=fonts['tiny'])
    stat2_width = stat2_bbox[2] - stat2_bbox[0]
    x_stat2 = (DISPLAY_WIDTH - stat2_width) // 2
    draw_black.text((x_stat2, y_footer), stat2, font=fonts['tiny'], fill=COLOR_BLACK)
    
    # Device Uptime/Placeholder for more info
    stat3 = f"Device: {os.uname().nodename}" # Gets the hostname
    stat3_bbox = draw_black.textbbox((0, 0), stat3, font=fonts['tiny'])
    stat3_width = stat3_bbox[2] - stat3_bbox[0]
    x_stat3 = DISPLAY_WIDTH - PADDING - stat3_width
    draw_black.text((x_stat3, y_footer), stat3, font=fonts['tiny'], fill=COLOR_BLACK)
    
    # The function should return both images
    return black_image, red_image

def update_display(black_image, red_image):
    """Update the e-paper display with two images"""
    try:
        # Assuming epd7in5_V2 or similar 3-color display
        from waveshare_epd import epd7in5_V2 as epd_module # Example 3-color module
        epd = epd_module.EPD()
        epd.init()
        epd.Clear()
        
        # Display expects a black/white image and a red image
        # The black image is passed as the first argument, the red image as the second
        epd.display(epd.getbuffer(black_image), epd.getbuffer(red_image))
        epd.sleep()
    except Exception as e:
        print(f"Display error: {e}")

def main():
    """Main function"""
    print("Creating dashboard...")
    
    # Create dashboard images
    black_image, red_image = create_dashboard()
    
    # Save preview (combine B/W and Red for a single color preview)
    # NOTE: This preview will NOT accurately show the e-paper colors but helps with layout.
    preview_image = Image.new('RGB', (DISPLAY_WIDTH, DISPLAY_HEIGHT), 'white')
    preview_draw = ImageDraw.Draw(preview_image)
    
    # Transfer black text to preview (black on white)
    black_data = black_image.getdata()
    for i, pixel in enumerate(black_data):
        if pixel == COLOR_BLACK:
            x = i % DISPLAY_WIDTH
            y = i // DISPLAY_WIDTH
            preview_draw.point((x, y), fill='black')
            
    # Transfer red text to preview (red on white)
    red_data = red_image.getdata()
    for i, pixel in enumerate(red_data):
        if pixel == COLOR_RED: # Check for the custom red color value
            x = i % DISPLAY_WIDTH
            y = i // DISPLAY_WIDTH
            preview_draw.point((x, y), fill='red') # Use 'red' for the RGB preview
            
    preview_image.save('/home/pi/epaper-dash/dashboard_preview_new.png')
    print("New preview saved to dashboard_preview_new.png (using simulated colors)")
    
    # Update display
    # update_display(black_image, red_image) # Uncomment this when running on the Pi with the display library
    
    print("Done!")

if __name__ == '__main__':
    main()