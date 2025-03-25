import requests
from bs4 import BeautifulSoup
import aiohttp
import asyncio
import json
from datetime import datetime
from dateutil.parser import parse
import os

BASE_URL = "https://jnovels.com/release-date/"
OUTPUT_FILE = "/data/light_novel_releases.json"  # Mounted volume for persistence

async def fetch_metadata(session, url):
    async with session.get(url) as response:
        html = await response.text()
        soup = BeautifulSoup(html, "html.parser")
        
        # Extract book cover (assuming an img tag with class or id)
        cover = soup.find("img", class_="book-cover") or soup.find("img")  # Adjust selector as needed
        cover_url = cover["src"] if cover else None
        
        # Extract description (assuming a div or p with class)
        desc = soup.find("div", class_="description") or soup.find("p")  # Adjust selector as needed
        description = desc.get_text(strip=True) if desc else "No description available"
        
        return {"book_cover": cover_url, "description": description}

async def scrape_page():
    response = requests.get(BASE_URL)
    soup = BeautifulSoup(response.text, "html.parser")
    
    tables = soup.find_all("table")
    releases = []
    
    # Load existing data for comparison
    existing_data = {}
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r") as f:
            existing_data = json.load(f)
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for table in tables:
            for row in table.find("tbody").find_all("tr"):
                cols = row.find_all("td")
                if len(cols) >= 5:
                    release_date = cols[0].text.strip()
                    title = cols[1].text.strip()
                    volume = cols[2].text.strip()
                    purchase_link = cols[3].find("a")["href"]
                    publisher = cols[3].text.strip()
                    release_type = cols[4].text.strip()
                    
                    # Parse date
                    try:
                        date_obj = parse(f"2025 {release_date}", dayfirst=False)
                        formatted_date = date_obj.strftime("%Y-%m-%d")
                    except ValueError:
                        formatted_date = release_date  # Fallback
                    
                    key = f"{title}-{volume}"
                    existing_entry = existing_data.get(key, {})
                    
                    entry = {
                        "title": title,
                        "volume_number": volume,
                        "release_date": formatted_date,
                        "publisher": publisher,
                        "book_link": purchase_link,
                        "release_type": release_type,
                        "last_updated": existing_entry.get("last_updated", datetime.utcnow().isoformat()),
                        "google_calendar_added": existing_entry.get("google_calendar_added", None)
                    }
                    
                    # Check for changes
                    if (existing_entry.get("release_date") != formatted_date or
                        existing_entry.get("publisher") != publisher or
                        existing_entry.get("release_type") != release_type):
                        entry["last_updated"] = datetime.utcnow().isoformat()
                    
                    tasks.append(fetch_metadata(session, purchase_link))
                    releases.append(entry)
        
        metadata = await asyncio.gather(*tasks)
        for i, meta in enumerate(metadata):
            releases[i].update(meta)
    
    # Save to JSON
    with open(OUTPUT_FILE, "w") as f:
        json.dump(releases, f, indent=2)

if __name__ == "__main__":
    asyncio.run(scrape_page())
    print(f"Scraped data saved to {OUTPUT_FILE}")