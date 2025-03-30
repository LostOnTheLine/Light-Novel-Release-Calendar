import os
import json
import time
from google.oauth2 import service_account
from googleapiclient.discovery import build
import googleapiclient.errors

CALENDAR_ID = os.getenv("CALENDAR_ID")
SCOPES = ["https://www.googleapis.com/auth/calendar"]

def clear_calendar(calendar_id, creds):
    print("Attempting to clear calendar")
    service = build("calendar", "v3", credentials=creds)
    page_token = None
    event_count = 0
    while True:
        try:
            events = service.events().list(calendarId=calendar_id, pageToken=page_token).execute()
            items = events.get("items", [])
            print(f"Found {len(items)} events in this page")
            for event in items:
                try:
                    service.events().delete(calendarId=calendar_id, eventId=event["id"]).execute()
                    print(f"Deleted event: {event['summary']}")
                    event_count += 1
                except googleapiclient.errors.HttpError as e:
                    if "rateLimitExceeded" in str(e):
                        wait_time = min(2 ** (event_count // 10), 60)  # Exponential backoff, max 60s
                        print(f"Rate limit hit, waiting {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        print(f"Error deleting event {event['summary']}: {str(e)}")
            page_token = events.get("nextPageToken")
            if not page_token:
                break
        except googleapiclient.errors.HttpError as e:
            if "rateLimitExceeded" in str(e):
                wait_time = min(2 ** (event