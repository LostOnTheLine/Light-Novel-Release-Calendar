import requests
from bs4 import BeautifulSoup
import aiohttp
import asyncio
import json
from datetime import datetime
from dateutil.parser import parse
import os
import time
import re

BASE_URL = "https://jnovels.com/release-date/"
OUTPUT_FILE = "/data/light_novel_releases.json"
SYNC_INTERVAL_HOURS = float(os.getenv("SYNC_INTERVAL_HOURS", 1))  # Default to 1 hour

async def fetch_metadata(session, url, volume):
    async with session.get(url) as response:
        html = await response.text()
        soup = BeautifulSoup(html, "html.parser")
        
        # Publisher-specific parsing
        if "j-novel.club" in url:
            rss = soup.find("link", type="application/rss+xml")
            rss_url = rss["href"] if rss else None
            cover = soup.find("img", src=re.compile(r"cdn\.j-novel\.club.*\d{3,4}/webp"))
            cover_url = cover["src"] if cover else None
            desc = soup.find("div", class_="ffukg03") or soup.find("p")
            description = desc.find_next("p").get_text(strip=True) if desc else "No description available"
        elif "sevenseasentertainment.com" in url:
            cover = soup.find("img", alt=re.compile(f".*Vol\. {volume}"))
            cover_url = cover["src"] if cover else None
            desc = soup.find("meta", {"name": "description"})
            description = desc["content"] if desc else "No description available"
            rss_url = None
        elif "yenpress.com" in url:
            cover = soup.find("img", class_="img-box-shadow")
            cover_url = cover["data-src"] if cover else None
            desc = soup.find("meta", {"name": "description"})
            description = desc["content"] if desc else "No description available"
            rss_url = None
        else:
            cover_url = None
            description = "No description available"
            rss_url = None
        
        return {"book_cover": cover_url, "description": description, "rss_feed": rss_url}

def extract_collection(title, volume):
    # Simple extraction: remove "Volume X" or "Vol. X"
    collection = re.sub(rf"\s*(Volume|Vol\.?)\s*{re.escape(volume)}\b", "", title, flags=re.IGNORECASE).strip()
    return collection

async def scrape_page():
    response = requests.get(BASE_URL)
    soup = BeautifulSoup(response.text, "html.parser")
    tables = soup.find_all("table")
    
    # Load existing data or initialize as empty list
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r") as f:
            existing_data = json.load(f)
    else:
        existing_data = []
    
    # Convert existing data to dict for lookup
    existing_dict = {f"{item['title']}-{item['volume_number']}": item for item in existing_data}
    
    releases = []
    current_year = "2025"  # Hardcoded for now; adjust if site changes
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for table in tables:
            prev_h1 = table.find_previous("h1")
            if prev_h1:
                current_year = prev_h1.text.split()[-1]  # e.g., "March 2025" -> "2025"
            
            for row in table.find("tbody").find_all("tr"):
                cols = row.find_all("td")
                if len(cols) >= 5:
                    release_date = cols[0].text.strip()  # e.g., "Mar 03"
                    title = cols[1].text.strip()  # Full release name
                    volume = cols[2].text.strip().replace("Volume ", "")  # Normalize to "1", "2", etc.
                    purchase_link = cols[3].find("a")["href"]
                    publisher = cols[3].text.strip()
                    release_type = cols[4].text.strip()
                    
                    date_obj = parse(f"{current_year} {release_date}", dayfirst=False)
                    formatted_date = date_obj.strftime("%Y-%m-%d")
                    collection = extract_collection(title, volume)
                    
                    key = f"{title}-{volume}"
                    existing_entry = existing_dict.get(key, {})
                    
                    entry = {
                        "title": title,
                        "collection": collection,
                        "volume_number": volume,
                        "release_date": formatted_date,
                        "publisher": publisher,
                        "book_link": purchase_link,
                        "release_type": release_type,
                        "last_updated": existing_entry.get("last_updated", datetime.utcnow().isoformat()),
                        "google_calendar_added": existing_entry.get("google_calendar_added", None)
                    }
                    
                    # Update last_updated only if data changed
                    if (existing_entry.get("release_date") != formatted_date or
                        existing_entry.get("publisher") != publisher or
                        existing_entry.get("release_type") != release_type):
                        entry["last_updated"] = datetime.utcnow().isoformat()
                    
                    releases.append(entry)
                    tasks.append(fetch_metadata(session, purchase_link, volume))
        
        metadata = await asyncio.gather(*tasks)
        for i, meta in enumerate(metadata):
            releases[i].update(meta)
    
    with open(OUTPUT_FILE, "w") as f:
        json.dump(releases, f, indent=2)
    print(f"Scraped data saved to {OUTPUT_FILE} at {datetime.utcnow()}")

if __name__ == "__main__":
    while True:
        asyncio.run(scrape_page())
        time.sleep(SYNC_INTERVAL_HOURS * 3600)