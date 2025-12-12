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
            return {'temp': '--', 'wind': '-', 'gust': '-', 'wind_dir': '', 'rain': 0, 'uv': 0, 'hourly': []}

        lat = getattr(config, 'LATITUDE', -33.8688)
        lon = getattr(config, 'LONGITUDE', 151.2093)

        url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&exclude=minutely,daily&units=metric&appid={api_key}"
        res = session.get(url, timeout=15).json()
        
        current = res.get('current', {})
        hourly = res.get('hourly', [])
        
        temp = round(current.get('temp', 0))
        uv = round(current.get('uvi', 0))
        
        wind_ms = current.get('wind_speed', 0)
        wind_kn = round(wind_ms * 1.94384)
        wind_deg = current.get('wind_deg', 0)
        wind_dir = get_wind_direction(wind_deg)
        
        gust_ms = current.get('wind_gust')
        if gust_ms is None and hourly:
             gust_ms = hourly[0].get('wind_gust', 0)
        if gust_ms is None: 
            gust_ms = wind_ms 
        gust_kn = round(gust_ms * 1.94384)
        
        rain_chance = 0
        hourly_data = []

        if hourly:
            pops = [h.get('pop', 0) for h in hourly[:12]]
            rain_chance = round(max(pops) * 100) if pops else 0
            
            for i in range(min(12, len(hourly))):
                hour_data = hourly[i]
                dt = datetime.fromtimestamp(hour_data['dt'])
                hourly_data.append({
                    'dt': dt,
                    'temp': hour_data['temp'],
                    'rain': hour_data.get('pop', 0) * 100
                })

        return {
            'temp': temp, 
            'wind': wind_kn, 
            'gust': gust_kn, 
            'wind_dir': wind_dir, 
            'rain': rain_chance, 
            'uv': uv, 
            'hourly': hourly_data
        }
    except Exception as e:
        logging.error(f"Weather error: {e}")
        return {'temp': '--', 'wind': '-', 'gust': '-', 'wind_dir': '', 'rain': 0, 'uv': 0, 'hourly': []}

def generate_weather_graph(hourly_data):
    if not hourly_data:
        return None

    times = [x['dt'] for x in hourly_data]
    temps = [x['temp'] for x in hourly_data]
    rains = [x['rain'] for x in hourly_data]

    # Optimized graph size
    fig, ax1 = plt.subplots(figsize=(5, 1.5), dpi=100)
    
    color = 'black'
    ax1.plot(times, temps, color=color, linewidth=2)
    ax1.tick_params(axis='y', labelcolor=color, labelsize=9)
    ax1.tick_params(axis='x', labelsize=9)
    
    date_form = DateFormatter("%H")
    ax1.xaxis.set_major_formatter(date_form)
    
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.spines['left'].set_visible(False)
    ax1.spines['bottom'].set_visible(False)

    if any(r > 0 for r in rains):
        ax2 = ax1.twinx()
        color = 'blue'
        ax2.bar(times, rains, color=color, alpha=0.3, width=0.04)
        ax2.set_ylim(0, 100)
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        ax2.spines['left'].set_visible(False)
        ax2.spines['bottom'].set_visible(False)
        ax2.set_yticks([]) 

    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', transparent=True)
    plt.close()
    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode('utf-8')

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
        
        # Local timezone for displaying departure time
        tz_name = getattr(config, 'TIMEZONE', "Australia/Sydney")
        local_tz = ZoneInfo(tz_name)
        
        for event in events[:4]:
            time_str = event.get('departureTimeEstimated', event.get('departureTimePlanned'))
            if not time_str: continue

            if time_str.endswith('Z'):
                time_str = time_str[:-1] + "+00:00"
            
            dep_dt = datetime.fromisoformat(time_str)
            # Convert to local time
            dep_local = dep_dt.astimezone(local_tz)
            
            # Format as HH:MM (e.g., 14:05)
            due_str = dep_local.strftime("%H:%M")
            
            # Check if it's past
            now = datetime.now(dep_dt.tzinfo)
            if dep_dt < now:
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
                    
                    time_str = dtstart.strftime("%I:%M%p").lower()
                    if time_str.startswith('0'): time_str = time_str[1:]
                    
                    date_str = dtstart.strftime("%a %d/%m")
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
    cached_weather_graph = None
    cached_news = []
    cached_calendar = []

    session = get_session()

    browser_path = find_chromium()
    if not browser_path:
        logging.error("Chromium not found. Install with: sudo apt install chromium")
        return

    while True:
        try:
            start_time = time.time()
            if (start_time - last_slow_update) >= SLOW_UPDATE_INTERVAL or cached_weather is None:
                logging.info("Fetching Slow Data...")
                cached_weather = get_weather(session)
                cached_weather_graph = generate_weather_graph(cached_weather.get('hourly', []))
                cached_news = get_news()
                cached_calendar = get_calendar(session)
                last_slow_update = start_time
            else:
                logging.info("Using cached Slow Data.")

            logging.info("Fetching Fast Data...")
            transport = get_transport(session)
            
            logging.info("Rendering HTML...")
            env = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(os.path.realpath(__file__))))
            template = env.get_template(TEMPLATE_FILE)
            
            html_out = template.render(
                current_date=datetime.now().strftime("%A, %d %b %H:%M"),
                current_weather=cached_weather,
                weather_graph=cached_weather_graph,
                news_items=cached_news,
                transport_data=transport,
                calendar_events=cached_calendar
            )
            
            logging.info("Generating Image...")
            
            # --- FIX: Render Taller & Crop ---
            # We render a slightly taller window (800x600) to ensure content doesn't get cut off
            # by Chromium's internal scrollbars/viewport logic, then we crop to 800x480.
            hti = Html2Image(browser_executable=browser_path, custom_flags=['--no-sandbox', '--hide-scrollbars', '--force-device-scale-factor=1', '--window-size=800,600'])
            
            # Generate temporary image
            temp_img = "temp_dashboard.png"
            hti.screenshot(html_str=html_out, css_file=CSS_FILE, save_as=temp_img, size=(800, 600))
            
            # Crop to exact E-Paper size using Pillow
            with Image.open(temp_img) as img:
                # Crop(left, top, right, bottom)
                cropped_img = img.crop((0, 0, 800, 480))
                cropped_img.save(OUTPUT_IMG)
            
            update_display()
            
            elapsed = time.time() - start_time
            sleep_time = max(0, 300 - elapsed) # 5 minutes
            logging.info(f"Update complete in {elapsed:.2f}s. Sleeping for {sleep_time:.2f}s...")
            time.sleep(sleep_time)

        except KeyboardInterrupt:
            logging.info("Dashboard stopped by user.")
            break
        except Exception as e:
            logging.error(f"Critical Loop Error: {e}")
            logging.info("Retrying in 60 seconds...")
            time.sleep(60)

if __name__ == "__main__":
    main()
