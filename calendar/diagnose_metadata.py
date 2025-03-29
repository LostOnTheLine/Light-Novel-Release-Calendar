import requests
from bs4 import BeautifulSoup
import json
import os
import sys
from google.oauth2 import service_account
from googleapiclient.discovery import build

SAMPLES = {
    "Seven Seas": "https://sevenseasentertainment.com/books/theres-no-freaking-way-ill-be-your-lover-unless-light-novel-vol-6/",
    "J-Novel Club": "https://j-novel.club/series/nia-liston-the-merciless-maiden#volume-5",
    "Yen Press": "https://yenpress.com/titles/9781975392536-re-starting-life-in-another-world-short-story-collection-vol-2-light-novel"
}

def diagnose_page(url):
    print(f"Diagnosing {url}")
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        data = {}
        
        # Seven Seas
        if "sevenseas" in url:
            data["description"] = soup.find("meta", {"name": "description"})["content"] if soup.find("meta", {"name": "description"}) else "N/A"
            data["cover"] = soup.find("img", alt=re.compile(r"Vol\. \d+"))["src"] if soup.find("img", alt=re.compile(r"Vol\. \d+")) else "N/A"
            data["genres"] = [tag.text for tag in soup.find_all("a", href=re.compile(r"/genre/"))]
        
        # J-Novel Club
        elif "j-novel.club" in url:
            data["description"] = soup.find("div", class_="ffukg03").find_next("p").text if soup.find("div", class_="ffukg03") else "N/A"
            data["cover"] = soup.find("img", src=re.compile(r"cdn\.j-novel\.club"))["src"] if soup.find("img", src=re.compile(r"cdn\.j-novel\.club")) else "N/A"
            data["rss"] = soup.find("link", type="application/rss+xml")["href"] if soup.find("link", type="application/rss+xml") else "N/A"
            data["genres"] = [tag.text for tag in soup.find_all("a", href=re.compile(r"/tags/"))]
        
        # Yen Press
        elif "yenpress" in url:
            data["description"] = soup.find("meta", {"name": "description"})["content"] if soup.find("meta", {"name": "description"}) else "N/A"
            data["cover"] = soup.find("img", class_="img-box-shadow")["data-src"] if soup.find("img", class_="img-box-shadow") else "N/A"
            data["genres"] = [tag.text for tag in soup.find_all("a", href=re.compile(r"/genre/"))]
        
        return data
    except Exception as e:
        print(f"Error diagnosing {url}: {str(e)}")
        return {"error": str(e)}

def clear_calendar(calendar_id, creds):
    print("Attempting to clear calendar")
    try:
        service = build("calendar", "v3", credentials=creds)
        events = service.events().list(calendarId=calendar_id).execute()
        for event in events.get("items", []):
            service.events().delete(calendarId=calendar_id, eventId=event["id"]).execute()
            print(f"Deleted event: {event['summary']}")
        print("Calendar cleared")
    except Exception as e:
        print(f"Error clearing calendar: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    print("Starting diagnosis")
    google_creds = os.getenv("GOOGLE_CREDENTIALS")
    calendar_id = os.getenv("CALENDAR_ID")
    
    if not google_creds or not calendar_id:
        print(f"Missing environment variables: GOOGLE_CREDENTIALS={bool(google_creds)}, CALENDAR_ID={bool(calendar_id)}")
        sys.exit(1)
    
    try:
        creds = service_account.Credentials.from_service_account_info(
            json.loads(google_creds),
            scopes=["https://www.googleapis.com/auth/calendar"]
        )
    except Exception as e:
        print(f"Error parsing GOOGLE_CREDENTIALS: {str(e)}")
        sys.exit(1)
    
    clear_calendar(calendar_id, creds)
    results = {publisher: diagnose_page(url) for publisher, url in SAMPLES.items()}
    
    with open("metadata_diagnosis.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Diagnosis complete, saved to metadata_diagnosis.json")