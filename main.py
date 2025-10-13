Last login: Mon Oct  6 21:09:16 on ttys000
/Users/xmclachlan/.zshrc:3: permission denied: /opt/homebrew/opt/chruby/share/chruby/chruby.sh
/Users/xmclachlan/.zshrc:5: command not found: chruby
xmclachlan@Xs-Air-2 ~ % ssh pi@raspberrypi 
Linux raspberrypi 6.12.47+rpt-rpi-v8 #1 SMP PREEMPT Debian 1:6.12.47-1+rpt1 (2025-09-16) aarch64

The programs included with the Debian GNU/Linux system are free software;
the exact distribution terms for each program are described in the
individual files in /usr/share/doc/*/copyright.

Debian GNU/Linux comes with ABSOLUTELY NO WARRANTY, to the extent
permitted by applicable law.
Last login: Tue Oct  7 22:56:20 2025 from 192.168.1.225
pi@raspberrypi:~ $ ls
dashboard_preview.png  epaper  epaper-dash
pi@raspberrypi:~ $ cd epaper-dash/
pi@raspberrypi:~/epaper-dash $ vim test2.py
pi@raspberrypi:~/epaper-dash $ python3 test2.py
INFO: Creating dashboard...
WARNING: Google Calendar API not installed. Install: pip install google-auth-oauthlib google-api-python-client
INFO: Preview saved to 'dashboard_preview.png'.
INFO: Updating e-paper display...
INFO: Display updated and sleeping.
INFO: Script finished.
pi@raspberrypi:~/epaper-dash $ source bin activate
-bash: bin: No such file or directory
pi@raspberrypi:~/epaper-dash $ ls
dashboard_layout.png  dashboard.log  dashboard_new_ui.png  dashboard_preview_fixed.png  dashboard_preview_new.png  dashboard_preview.png  epaper  lib  main.py  output  README.md  requirements.txt  test2.py  test.py
pi@raspberrypi:~/epaper-dash $ cd epaper
pi@raspberrypi:~/epaper-dash/epaper $ ls
bin  include  lib  lib64  pyvenv.cfg
pi@raspberrypi:~/epaper-dash/epaper $ cd bin
pi@raspberrypi:~/epaper-dash/epaper/bin $ ls
activate  activate.csh  activate.fish  Activate.ps1  pip  pip3  pip3.13  python  python3  python3.13
pi@raspberrypi:~/epaper-dash/epaper/bin $ cd ..
pi@raspberrypi:~/epaper-dash/epaper $ cd ..
pi@raspberrypi:~/epaper-dash $ source epaper/bin/activate
(epaper) pi@raspberrypi:~/epaper-dash $ pip install google-auth-oauthlib
Collecting google-auth-oauthlib
  Downloading google_auth_oauthlib-1.2.2-py3-none-any.whl.metadata (2.7 kB)
Collecting google-auth>=2.15.0 (from google-auth-oauthlib)
  Downloading google_auth-2.41.1-py2.py3-none-any.whl.metadata (6.6 kB)
Collecting requests-oauthlib>=0.7.0 (from google-auth-oauthlib)
  Downloading requests_oauthlib-2.0.0-py2.py3-none-any.whl.metadata (11 kB)
Collecting cachetools<7.0,>=2.0.0 (from google-auth>=2.15.0->google-auth-oauthlib)
  Downloading cachetools-6.2.1-py3-none-any.whl.metadata (5.5 kB)
Collecting pyasn1-modules>=0.2.1 (from google-auth>=2.15.0->google-auth-oauthlib)
  Downloading pyasn1_modules-0.4.2-py3-none-any.whl.metadata (3.5 kB)
Collecting rsa<5,>=3.1.4 (from google-auth>=2.15.0->google-auth-oauthlib)
  Downloading rsa-4.9.1-py3-none-any.whl.metadata (5.6 kB)
Collecting pyasn1>=0.1.3 (from rsa<5,>=3.1.4->google-auth>=2.15.0->google-auth-oauthlib)
  Downloading pyasn1-0.6.1-py3-none-any.whl.metadata (8.4 kB)
Requirement already satisfied: oauthlib>=3.0.0 in /usr/lib/python3/dist-packages (from requests-oauthlib>=0.7.0->google-auth-oauthlib) (3.2.2)
Requirement already satisfied: requests>=2.0.0 in /usr/lib/python3/dist-packages (from requests-oauthlib>=0.7.0->google-auth-oauthlib) (2.32.3)
Requirement already satisfied: charset_normalizer<4,>=2 in /usr/lib/python3/dist-packages (from requests>=2.0.0->requests-oauthlib>=0.7.0->google-auth-oauthlib) (3.4.2)
Requirement already satisfied: idna<4,>=2.5 in /usr/lib/python3/dist-packages (from requests>=2.0.0->requests-oauthlib>=0.7.0->google-auth-oauthlib) (3.10)
Requirement already satisfied: urllib3<3,>=1.21.1 in /usr/lib/python3/dist-packages (from requests>=2.0.0->requests-oauthlib>=0.7.0->google-auth-oauthlib) (2.3.0)
Requirement already satisfied: certifi>=2017.4.17 in /usr/lib/python3/dist-packages (from requests>=2.0.0->requests-oauthlib>=0.7.0->google-auth-oauthlib) (2025.1.31)
Downloading google_auth_oauthlib-1.2.2-py3-none-any.whl (19 kB)
Downloading google_auth-2.41.1-py2.py3-none-any.whl (221 kB)
Downloading cachetools-6.2.1-py3-none-any.whl (11 kB)
Downloading rsa-4.9.1-py3-none-any.whl (34 kB)
Downloading pyasn1-0.6.1-py3-none-any.whl (83 kB)
Downloading pyasn1_modules-0.4.2-py3-none-any.whl (181 kB)
Downloading requests_oauthlib-2.0.0-py2.py3-none-any.whl (24 kB)
Installing collected packages: pyasn1, cachetools, rsa, requests-oauthlib, pyasn1-modules, google-auth, google-auth-oauthlib
Successfully installed cachetools-6.2.1 google-auth-2.41.1 google-auth-oauthlib-1.2.2 pyasn1-0.6.1 pyasn1-modules-0.4.2 requests-oauthlib-2.0.0 rsa-4.9.1
(epaper) pi@raspberrypi:~/epaper-dash $ pip install google-api-python-client
Collecting google-api-python-client
  Downloading google_api_python_client-2.184.0-py3-none-any.whl.metadata (7.0 kB)
Collecting httplib2<1.0.0,>=0.19.0 (from google-api-python-client)
  Downloading httplib2-0.31.0-py3-none-any.whl.metadata (2.2 kB)
Requirement already satisfied: google-auth!=2.24.0,!=2.25.0,<3.0.0,>=1.32.0 in ./epaper/lib/python3.13/site-packages (from google-api-python-client) (2.41.1)
Collecting google-auth-httplib2<1.0.0,>=0.2.0 (from google-api-python-client)
  Downloading google_auth_httplib2-0.2.0-py2.py3-none-any.whl.metadata (2.2 kB)
Collecting google-api-core!=2.0.*,!=2.1.*,!=2.2.*,!=2.3.0,<3.0.0,>=1.31.5 (from google-api-python-client)
  Downloading google_api_core-2.26.0-py3-none-any.whl.metadata (3.2 kB)
Requirement already satisfied: uritemplate<5,>=3.0.1 in /usr/lib/python3/dist-packages (from google-api-python-client) (4.1.1)
Collecting googleapis-common-protos<2.0.0,>=1.56.2 (from google-api-core!=2.0.*,!=2.1.*,!=2.2.*,!=2.3.0,<3.0.0,>=1.31.5->google-api-python-client)
  Downloading googleapis_common_protos-1.70.0-py3-none-any.whl.metadata (9.3 kB)
Collecting protobuf!=3.20.0,!=3.20.1,!=4.21.0,!=4.21.1,!=4.21.2,!=4.21.3,!=4.21.4,!=4.21.5,<7.0.0,>=3.19.5 (from google-api-core!=2.0.*,!=2.1.*,!=2.2.*,!=2.3.0,<3.0.0,>=1.31.5->google-api-python-client)
  Downloading protobuf-6.32.1-cp39-abi3-manylinux2014_aarch64.whl.metadata (593 bytes)
Collecting proto-plus<2.0.0,>=1.22.3 (from google-api-core!=2.0.*,!=2.1.*,!=2.2.*,!=2.3.0,<3.0.0,>=1.31.5->google-api-python-client)
  Downloading proto_plus-1.26.1-py3-none-any.whl.metadata (2.2 kB)
Requirement already satisfied: requests<3.0.0,>=2.18.0 in /usr/lib/python3/dist-packages (from google-api-core!=2.0.*,!=2.1.*,!=2.2.*,!=2.3.0,<3.0.0,>=1.31.5->google-api-python-client) (2.32.3)
Requirement already satisfied: cachetools<7.0,>=2.0.0 in ./epaper/lib/python3.13/site-packages (from google-auth!=2.24.0,!=2.25.0,<3.0.0,>=1.32.0->google-api-python-client) (6.2.1)
Requirement already satisfied: pyasn1-modules>=0.2.1 in ./epaper/lib/python3.13/site-packages (from google-auth!=2.24.0,!=2.25.0,<3.0.0,>=1.32.0->google-api-python-client) (0.4.2)
Requirement already satisfied: rsa<5,>=3.1.4 in ./epaper/lib/python3.13/site-packages (from google-auth!=2.24.0,!=2.25.0,<3.0.0,>=1.32.0->google-api-python-client) (4.9.1)
Collecting pyparsing<4,>=3.0.4 (from httplib2<1.0.0,>=0.19.0->google-api-python-client)
  Downloading pyparsing-3.2.5-py3-none-any.whl.metadata (5.0 kB)
Requirement already satisfied: charset_normalizer<4,>=2 in /usr/lib/python3/dist-packages (from requests<3.0.0,>=2.18.0->google-api-core!=2.0.*,!=2.1.*,!=2.2.*,!=2.3.0,<3.0.0,>=1.31.5->google-api-python-client) (3.4.2)
Requirement already satisfied: idna<4,>=2.5 in /usr/lib/python3/dist-packages (from requests<3.0.0,>=2.18.0->google-api-core!=2.0.*,!=2.1.*,!=2.2.*,!=2.3.0,<3.0.0,>=1.31.5->google-api-python-client) (3.10)
Requirement already satisfied: urllib3<3,>=1.21.1 in /usr/lib/python3/dist-packages (from requests<3.0.0,>=2.18.0->google-api-core!=2.0.*,!=2.1.*,!=2.2.*,!=2.3.0,<3.0.0,>=1.31.5->google-api-python-client) (2.3.0)
Requirement already satisfied: certifi>=2017.4.17 in /usr/lib/python3/dist-packages (from requests<3.0.0,>=2.18.0->google-api-core!=2.0.*,!=2.1.*,!=2.2.*,!=2.3.0,<3.0.0,>=1.31.5->google-api-python-client) (2025.1.31)
Requirement already satisfied: pyasn1>=0.1.3 in ./epaper/lib/python3.13/site-packages (from rsa<5,>=3.1.4->google-auth!=2.24.0,!=2.25.0,<3.0.0,>=1.32.0->google-api-python-client) (0.6.1)
Downloading google_api_python_client-2.184.0-py3-none-any.whl (14.3 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 14.3/14.3 MB 7.1 MB/s eta 0:00:00
Downloading google_api_core-2.26.0-py3-none-any.whl (162 kB)
Downloading google_auth_httplib2-0.2.0-py2.py3-none-any.whl (9.3 kB)
Downloading googleapis_common_protos-1.70.0-py3-none-any.whl (294 kB)
Downloading httplib2-0.31.0-py3-none-any.whl (91 kB)
Downloading proto_plus-1.26.1-py3-none-any.whl (50 kB)
Downloading protobuf-6.32.1-cp39-abi3-manylinux2014_aarch64.whl (322 kB)
Downloading pyparsing-3.2.5-py3-none-any.whl (113 kB)
Installing collected packages: pyparsing, protobuf, proto-plus, httplib2, googleapis-common-protos, google-auth-httplib2, google-api-core, google-api-python-client
Successfully installed google-api-core-2.26.0 google-api-python-client-2.184.0 google-auth-httplib2-0.2.0 googleapis-common-protos-1.70.0 httplib2-0.31.0 proto-plus-1.26.1 protobuf-6.32.1 pyparsing-3.2.5
(epaper) pi@raspberrypi:~/epaper-dash $ pwd
/home/pi/epaper-dash
(epaper) pi@raspberrypi:~/epaper-dash $ ls
client_secret_601029804067-u3lhah9d0643ndrm6vu0prkbgqfvj128.apps.googleusercontent.com.json  dashboard_layout.png  dashboard.log  dashboard_new_ui.png  dashboard_preview_fixed.png  dashboard_preview_new.png  dashboard_preview.png  epaper  lib  main.py  output  README.md  requirements.txt  test2.py  test.py
(epaper) pi@raspberrypi:~/epaper-dash $ python3 test2.py
INFO: Creating dashboard...
ERROR: Calendar API error: [Errno 2] No such file or directory: 'credentials.json'
INFO: Preview saved to 'dashboard_preview.png'.
INFO: Updating e-paper display...
INFO: Display updated and sleeping.
INFO: Script finished.
(epaper) pi@raspberrypi:~/epaper-dash $ mv client_secret_601029804067-u3lhah9d0643ndrm6vu0prkbgqfvj128.apps.googleusercontent.com.json credentials.json
(epaper) pi@raspberrypi:~/epaper-dash $ python3 test2.py
INFO: Creating dashboard...
ERROR: Calendar API error: could not locate runnable browser
INFO: Preview saved to 'dashboard_preview.png'.
INFO: Updating e-paper display...
INFO: Display updated and sleeping.
INFO: Script finished.
(epaper) pi@raspberrypi:~/epaper-dash $ vim main.py
(epaper) pi@raspberrypi:~/epaper-dash $ vim test2.py

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
                                                                                                                                                                                                                                                                                                                    390,10        Bot

