# An Epaper Dashboard

## Hardware

- Raspberry Pi 4, 4gb
- Waveshare 7.5in Epaper (H)

## What it does

- Displays the time, weather and live temperature from a DHT11
- Pulls Calendar events from Google Calendar and displays the next 3 events
- Lists the next 3 departures from the local bus stop
- Lists the next scheduled Reminders from Apple Reminders
- Lists the top headlines from a FreshRSS feed

## How?

Core Components:

Language: Python 3
Display Driver: Waveshare library for your specific 7.5" model
Web Framework: Flask (lightweight) running locally for data collection
Image Generation: Pillow (PIL) for composing the dashboard layout
Scheduling: systemd timers or cron jobs

Data Source Libraries:

Google Calendar: google-api-python-client, google-auth
Apple Reminders: Since you're on RPi, you'll need iCloud API via pyicloud library or sync via CalDAV
RSS: feedparser
DHT11 Sensor: Adafruit_DHT or adafruit-circuitpython-dht
Weather API: OpenWeatherMap or similar (optional, since you have the sensor)
Bus departures: Depends on your transit agency's API

dashboard/
├── collectors/          # Individual data fetchers
│   ├── calendar.py
│   ├── reminders.py
│   ├── bus.py
│   ├── rss.py
│   ├── weather.py
│   └── sensor.py
├── renderer/           # Display rendering
│   ├── layout.py
│   └── display.py
├── data/              # Cached data
│   └── dashboard_data.json
├── config.py          # API keys, settings
└── main.py           # Orchestrator

Workflow

Data Collection (runs every 5-15 minutes):

Each collector module fetches its data
Writes to dashboard_data.json
Includes timestamps and error handling


Display Rendering (runs every 15-30 minutes):

Reads from dashboard_data.json
Uses Pillow to create a composite image
Sends to e-paper display
E-paper goes to sleep to save power


Sensor Reading (continuous or frequent):

DHT11 reads happen more frequently
Store in JSON for display to pick up
