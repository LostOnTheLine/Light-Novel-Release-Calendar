import requests
from bs4 import BeautifulSoup
import json

SAMPLES = {
    "Seven Seas": "https://sevenseasentertainment.com/books/theres-no-freaking-way-ill-be-your-lover-unless-light-novel-vol-6/",
    "J-Novel Club": "https://j-novel.club/series/nia-liston-the-merciless-maiden#volume-5",
    "Yen Press": "https://yenpress.com/titles/9781975392536-re-starting-life-in-another-world-short-story-collection-vol-2-light-novel"
}

def diagnose_page(url):
    response = requests.get(url)
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

def clear_calendar(calendar_id, creds):
    service = build("calendar", "v3", credentials=creds)
    events = service.events().list(calendarId=calendar_id).execute()
    for event in events.get("items", []):
        service.events().delete(calendarId=calendar_id, eventId=event["id"]).execute()
    print("Calendar cleared")

if __name__ == "__main__":
    creds = service_account.Credentials.from_service_account_info(
        json.loads(os.getenv("GOOGLE_CREDENTIALS")),
        scopes=["https://www.googleapis.com/auth/calendar"]
    )
    clear_calendar(os.getenv("CALENDAR_ID"), creds)
    
    results = {publisher: diagnose_page(url) for publisher, url in SAMPLES.items()}
    with open("metadata_diagnosis.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Diagnosis complete, saved to metadata_diagnosis.json")