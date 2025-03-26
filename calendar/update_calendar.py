import json
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dateutil.parser import parse
from datetime import datetime

JSON_FILE = "light_novel_releases.json"
CALENDAR_ID = os.getenv("CALENDAR_ID")
SCOPES = ["https://www.googleapis.com/auth/calendar"]

# Load Service Account credentials from GOOGLE_CREDENTIALS environment variable
creds = service_account.Credentials.from_service_account_info(
    json.loads(os.getenv("GOOGLE_CREDENTIALS")),
    scopes=SCOPES
)

service = build("calendar", "v3", credentials=creds)

with open(JSON_FILE, "r") as f:
    releases = json.load(f)

updated = False
for release in releases:
    if not release.get("google_calendar_added"):
        event = {
            "summary": f"{release['title']} Vol. {release['volume_number']} ({release['publisher']})",
            "description": release["description"],
            "start": {"date": release["release_date"], "timeZone": "UTC"},
            "end": {"date": release["release_date"], "timeZone": "UTC"},
        }
        service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        release["google_calendar_added"] = datetime.utcnow().isoformat()
        updated = True
    elif parse(release["last_updated"]) > parse(release["google_calendar_added"]):
        event = {
            "summary": f"{release['title']} Vol. {release['volume_number']} ({release['publisher']})",
            "description": release["description"],
            "start": {"date": release["release_date"], "timeZone": "UTC"},
            "end": {"date": release["release_date"], "timeZone": "UTC"},
        }
        service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        release["google_calendar_added"] = datetime.utcnow().isoformat()
        updated = True

if updated:
    with open(JSON_FILE, "w") as f:
        json.dump(releases, f, indent=2)

print("Calendar updated")