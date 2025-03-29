import json
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dateutil.parser import parse
from datetime import datetime
import time
import googleapiclient.errors

JSON_FILE = "data/light_novel_releases.json"
CONFIG_FILE = "calendar/config.json"
CALENDAR_ID = os.getenv("CALENDAR_ID")
SCOPES = ["https://www.googleapis.com/auth/calendar"]

# Load Service Account credentials from GOOGLE_CREDENTIALS environment variable
creds = service_account.Credentials.from_service_account_info(
    json.loads(os.getenv("GOOGLE_CREDENTIALS")),
    scopes=SCOPES
)
service = build("calendar", "v3", credentials=creds)

# Load publisher config
with open(CONFIG_FILE, "r") as f:
    config = json.load(f)
publisher_colors = config["publishers"]

# Initialize file if it doesn’t exist
def insert_event_with_retry(event, max_retries=5):
    retries = 0
    while retries < max_retries:
        try:
            service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
            return True
        except googleapiclient.errors.HttpError as e:
            if e.resp.status == 403 and "rateLimitExceeded" in str(e):
                wait_time = 2 ** retries  # Exponential backoff: 1s, 2s, 4s, 8s, 16s
                print(f"Rate limit exceeded, retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                retries += 1
            else:
                raise e
    print("Max retries reached; skipping event")
    return False

if not os.path.exists(JSON_FILE):
    os.makedirs(os.path.dirname(JSON_FILE), exist_ok=True)
    with open(JSON_FILE, "w") as f:
        json.dump([], f)

with open(JSON_FILE, "r") as f:
    releases = json.load(f)

updated = False
for release in releases:
    publisher_config = publisher_colors.get(release["publisher"], publisher_colors["Default"])
    color_id = publisher_config["colorId"]
    hex_color = publisher_config["color"]
    rss_link = release.get("rss_feed", "")
    rss_icon = f'<a href="{rss_link}"><img src="https://upload.wikimedia.org/wikipedia/commons/4/43/Feed-icon.svg" width="16" height="16" alt="RSS"></a>' if rss_link else ""
    
    description_html = (
        f'<div style="display: flex; justify-content: space-between;">'
        f'<div style="text-align: left;">'
        f'Volume {release["volume_number"]} {rss_icon}<br>'
        f'<a href="{release["book_link"]}">{release["publisher"]}</a><br>'
        f'{release["release_type"]}<br>'
        f'{release["description"]}'
        f'</div>'
        f'<div style="text-align: right;">'
        f'<img src="{release["book_cover"]}" style="max-width: 150px;" alt="Book Cover">'
        f'</div>'
        f'</div>'
    )

    event = {
        "summary": release["title"],
        "description": description_html,
        "start": {"date": release["release_date"], "timeZone": "UTC"},
        "end": {"date": release["release_date"], "timeZone": "UTC"},
        "colorId": color_id,  # Use predefined colorId
        "extendedProperties": {
            "private": {"customColor": hex_color}  # Store hex for reference
        }
    }

    if not release.get("google_calendar_added"):
        if insert_event_with_retry(event):
            release["google_calendar_added"] = datetime.utcnow().isoformat()
            updated = True
    elif parse(release["last_updated"]) > parse(release["google_calendar_added"]):
        if insert_event_with_retry(event):
            release["google_calendar_added"] = datetime.utcnow().isoformat()
            updated = True

if updated:
    with open(JSON_FILE, "w") as f:
        json.dump(releases, f, indent=2)

print("Calendar updated")