#!/usr/bin/env python3
import sys
import os
import time
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import feedparser
import jinja2
from html2image import Html2Image
from datetime import datetime, timedelta, timezone
from icalendar import Calendar
from PIL import Image
import shutil
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
import base64
import io
from zoneinfo import ZoneInfo

# --- SETUP PATHS ---
libdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

# Import Config
try:
    import config
except ImportError:
    logging.error("config.py not found. Please create it.")
    sys.exit(1)

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')

# --- CONFIGURATION ---
TEMPLATE_FILE = "dashboard_template.html"
CSS_FILE = "style.css"
OUTPUT_IMG = "dashboard_output.png"

# --- NETWORK SESSION SETUP ---
def get_session():
    session = requests.Session()
    retry = Retry(total=5, read=5, connect=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

# --- DATA FETCHERS ---

def get_wind_direction(degrees):
    if degrees is None: return ""
    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                  "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    idx = round(degrees / 22.5) % 16
    return directions[idx]

def get_weather(session):
    try:
        api_key = getattr(config, 'OWM_API_KEY', '')
        if not api_key or "YOUR_" in api_key:
            return {'current': {'temp': '-', 'desc': 'No Key'}, 'forecast': []}

        lat = getattr(config, 'LATITUDE', -33.8688)
        lon = getattr(config, 'LONGITUDE', 151.2093)

        url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&exclude=minutely,daily,alerts&units=metric&appid={api_key}"
        res = session.get(url, timeout=15).json()
        
        current = res.get('current', {})
        hourly = res.get('hourly', [])
        
        # Current
        temp = round(current.get('temp', 0))
        desc = current.get('weather', [{}])[0].get('main', 'Unknown')
        
        wind_ms = current.get('wind_speed', 0)
        wind_kn = round(wind_ms * 1.94384)
        wind_deg = current.get('wind_deg', 0)
        wind_dir = get_wind_direction(wind_deg)
        
        gust_ms = current.get('wind_gust', wind_ms)
        gust_kn = round(gust_ms * 1.94384)

        weather_data = {
            'temp': temp,
            'desc': desc,
            'wind': f"{wind_kn}kt {wind_dir}",
            'gust': f"{gust_kn}kt",
            'uv': round(current.get('uvi', 0)),
            'rain_prob': 0,
            # Placeholder for Tides (Not in OWM)
            'tide_high': "14:30",
            'tide_low': "20:45" 
        }

        # 3-Hour Forecast
        forecast_items = []
        if hourly:
            # Next 3 hours
            for i in range(1, 4): 
                if i >= len(hourly): break
                h = hourly[i]
                dt = datetime.fromtimestamp(h['dt'])
                
                pop = round(h.get('pop', 0) * 100)
                t = round(h.get('temp', 0))
                
                code = h.get('weather', [{}])[0].get('id', 800)
                icon = "sun"
                if 200 <= code < 600: icon = "rain"
                elif 600 <= code < 700: icon = "snow"
                elif code == 800: icon = "sun"
                else: icon = "cloud"

                forecast_items.append({
                    'time': dt.strftime("%I%p").lstrip("0").lower(),
                    'temp': t,
                    'pop': pop,
                    'icon': icon
                })
            
            weather_data['rain_prob'] = round(max([h.get('pop', 0) for h in hourly[:12]]) * 100)

        return {'current': weather_data, 'forecast': forecast_items}

    except Exception as e:
        logging.error(f"Weather error: {e}")
        return {'current': {'temp': '-', 'desc': 'Error'}, 'forecast': []}

def get_transport(session):
    api_key = getattr(config, 'TFNSW_API_KEY', '')
    stop_id = getattr(config, 'BUS_STOP_ID', '')

    if not api_key or "YOUR_" in api_key:
        return [{"route": "ERR", "destination": "Set API Key", "due": "--"}]
        
    url = f"https://api.transport.nsw.gov.au/v1/tp/departure_mon?outputFormat=rapidJSON&coordOutputFormat=EPSG%3A4326&mode=direct&type_dm=stop&name_dm={stop_id}&depArrMacro=dep&TfNSWDM=true"
    headers = {"Authorization": f"apikey {api_key}"}
    
    departures = []
    try:
        resp = session.get(url, headers=headers, timeout=15).json()
        events = resp.get('stopEvents', [])
        
        tz_name = getattr(config, 'TIMEZONE', "Australia/Sydney")
        local_tz = ZoneInfo(tz_name)
        now_local = datetime.now(local_tz)
        
        for event in events[:4]:
            time_str = event.get('departureTimeEstimated', event.get('departureTimePlanned'))
            if not time_str: continue

            if time_str.endswith('Z'):
                time_str = time_str[:-1] + "+00:00"
            
            dep_dt = datetime.fromisoformat(time_str)
            if dep_dt.tzinfo is None:
                dep_dt = dep_dt.replace(tzinfo=timezone.utc)
            
            dep_local = dep_dt.astimezone(local_tz)
            
            due_str = dep_local.strftime("%H:%M")
            
            if dep_local < now_local:
                continue 
            
            route = event['transportation']['number']
            dest = event['transportation']['destination']['name'].split(",")[0]
            
            departures.append({
                'route': route,
                'destination': dest[:15],
                'due': due_str
            })
    except Exception as e:
        logging.error(f"Transport error: {e}")
        
    return departures if departures else [{"route": "--", "destination": "No services", "due": ""}]

def get_news():
    headlines = []
    sources = [
        ("ABC", "abc", "https://www.abc.net.au/news/feed/51120/rss.xml"),
        ("Gdn", "guardian", "https://www.theguardian.com/au/rss")
    ]
    
    for name, code, url in sources:
        try:
            feed = feedparser.parse(url)
            if feed.entries:
                headlines.append({'source': name, 'source_code': code, 'title': feed.entries[0].title})
        except: pass
        
    return headlines

def get_calendar(session):
    events = []
    cal_url = getattr(config, 'CALENDAR_URL', None) or getattr(config, 'CALENDAR_ICS_URL', None)
    
    if not cal_url:
        return []

    try:
        resp = session.get(cal_url, timeout=15)
        cal = Calendar.from_ical(resp.text)
        
        tz_name = getattr(config, 'TIMEZONE', "Australia/Sydney")
        local_tz = ZoneInfo(tz_name)
        now = datetime.now(local_tz)
        
        for component in cal.walk():
            if component.name == "VEVENT":
                summary = str(component.get('summary'))
                dtstart = component.get('dtstart').dt
                dtend = component.get('dtend').dt if component.get('dtend') else None
                
                if type(dtstart) is datetime:
                    if dtstart.tzinfo:
                        dtstart = dtstart.astimezone(local_tz)
                    else:
                        dtstart = dtstart.replace(tzinfo=local_tz)
                    
                    if dtend:
                        if dtend.tzinfo:
                            dtend = dtend.astimezone(local_tz)
                        else:
                            dtend = dtend.replace(tzinfo=local_tz)
                    
                    time_str = dtstart.strftime("%I:%M%p").lower()
                    if time_str.startswith('0'): time_str = time_str[1:]
                    
                    date_str = dtstart.strftime("%a %d/%m")
                    
                    if dtend:
                        end_str = dtend.strftime("%I:%M%p").lower()
                        if end_str.startswith('0'): end_str = end_str[1:]
                        time_str += f" - {end_str}" # Added End Time
                else:
                    dtstart = datetime.combine(dtstart, datetime.min.time(), tzinfo=local_tz)
                    time_str = "All Day"
                    date_str = dtstart.strftime("%a %d/%m")

                if now < dtstart:
                    if len(summary) > 22:
                        summary = summary[:20] + ".."
                    
                    events.append({'date': date_str, 'time': time_str, 'summary': summary, 'dt': dtstart})
        
        events.sort(key=lambda x: x['dt'])
    except Exception as e:
        logging.error(f"Calendar error: {e}")
    return events[:4]

# --- RENDER & DISPLAY ---

def find_chromium():
    paths = ["/usr/bin/chromium", "/usr/bin/chromium-browser", "/usr/lib/chromium-browser/chromium-browser"]
    for p in paths:
        if shutil.which(p): return p
    return None

def update_display():
    try:
        from waveshare_epd import epd7in5h
        epd = epd7in5h.EPD()
        epd.init()
        logging.info("Processing Image...")
        Himage = Image.open(OUTPUT_IMG)
        if getattr(config, 'ROTATE_180', False):
            Himage = Himage.rotate(180)
        logging.info("Sending to Display...")
        epd.display(epd.getbuffer(Himage))
        logging.info("Sleeping Display...")
        epd.sleep()
    except ImportError:
        logging.warning("Waveshare library not found. Running in simulation mode.")
    except Exception as e:
        logging.error(f"Display Error: {e}")

def main():
    logging.info("Starting Dashboard Automator...")
    SLOW_UPDATE_INTERVAL = 1800 
    last_slow_update = 0
    cached_weather = None
    cached_news = []
    cached_calendar = []

    session = get_session()

    browser_path = find_chromium()
    if not browser_path:
        logging.error("Chromium not found.")
        return

    while True:
        try:
            start_time = time.time()
            if (start_time - last_slow_update) >= SLOW_UPDATE_INTERVAL or cached_weather is None:
                logging.info("Fetching Slow Data...")
                cached_weather = get_weather(session)
                cached_news = get_news()
                cached_calendar = get_calendar(session)
                last_slow_update = start_time
            
            logging.info("Fetching Fast Data...")
            transport = get_transport(session)
            
            logging.info("Rendering HTML...")
            env = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(os.path.realpath(__file__))))
            template = env.get_template(TEMPLATE_FILE)
            
            html_out = template.render(
                current_date=datetime.now().strftime("%A, %d %B"),
                current_time=datetime.now().strftime("%H:%M"),
                weather=cached_weather,
                news_items=cached_news,
                transport_data=transport,
                calendar_events=cached_calendar
            )
            
            logging.info("Generating Image...")
            
            # --- FIX: Render Taller & Crop ---
            # Render a larger window (800x600) to ensure no scrolling/cutoff
            # Then crop to exactly 800x480
            hti = Html2Image(browser_executable=browser_path, 
                           custom_flags=['--no-sandbox', '--hide-scrollbars', '--force-device-scale-factor=1', '--window-size=800,600'])
            
            temp_file = "temp_render.png"
            hti.screenshot(html_str=html_out, css_file=CSS_FILE, save_as=temp_file, size=(800, 600))
            
            with Image.open(temp_file) as img:
                # Crop(left, top, right, bottom) - Strict 800x480
                cropped_img = img.crop((0, 0, 800, 480))
                # Ensure RGB mode for driver
                rgb_img = cropped_img.convert('RGB')
                rgb_img.save(OUTPUT_IMG)
            
            update_display()
            
            elapsed = time.time() - start_time
            sleep_time = max(0, 300 - elapsed)
            logging.info(f"Update complete. Sleeping for {sleep_time:.0f}s...")
            time.sleep(sleep_time)

        except KeyboardInterrupt:
            break
        except Exception as e:
            logging.error(f"Loop Error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()