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

# Collection override for grouping series (expand as needed)
COLLECTION_OVERRIDES = {
    r"The Sword of Truth|Sword of Truth": "The Sword of Truth"
}

async def fetch_metadata(session, url, volume_number):
    async with session.get(url) as response:
        html = await response.text()
        soup = BeautifulSoup(html, "html.parser")
        
        # Cover URL and description based on publisher
        cover_url = None
        description = "No description available"
        rss_feed = None
        
        if "j-novel.club" in url:
            cover = soup.find("img", src=re.compile(r"cdn\.j-novel\.club.*\.(jpg|webp)"))
            cover_url = cover["src"] if cover else None
            desc = soup.find("meta", property="og:description")
            description = desc["content"] if desc else soup.find("p").get_text(strip=True) if soup.find("p") else "No description available"
            rss = soup.find("link", type="application/rss+xml")
            rss_feed = rss["href"] if rss else None
        elif "sevenseasentertainment.com" in url:
            cover = soup.find("div", id="volume-cover").find("img") if soup.find("div", id="volume-cover") else None
            cover_url = cover["src"] if cover else None
            desc = soup.find("meta", attrs={"name": "description"})
            description = desc["content"] if desc else "No description available"
        elif "yenpress.com" in url:
            cover = soup.find("div", class_="book-cover-img").find("img") if soup.find("div", class_="book-cover-img") else None
            cover_url = cover["data-src"] if cover and "data-src" in cover.attrs else cover["src"] if cover else None
            desc = soup.find("meta", attrs={"name": "description"})
            description = desc["content"] if desc else "No description available"
        
        return {"book_cover": cover_url, "description": description, "rss_feed": rss_feed}

def extract_collection(title, volume_number):
    # Remove volume from title to guess collection
    volume_str = f"Volume {volume_number}" if not volume_number.isdigit() else f"Vol. {volume_number}"
    collection = re.sub(rf"\s*(Volume\s*{volume_number}|Vol\.\s*{volume_number})\b", "", title, flags=re.IGNORECASE).strip()
    
    # Apply overrides
    for pattern, coll_name in COLLECTION_OVERRIDES.items():
        if re.search(pattern, title, re.IGNORECASE):
            return coll_name
    return collection

async def scrape_page():
    response = requests.get(BASE_URL)
    soup = BeautifulSoup(response.text, "html.parser")
    tables = soup.find_all("table")
    releases = []
    
    # Load existing data or initialize as list
    existing_data = []
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r") as f:
            existing_data = json.load(f)
    existing_dict = {f"{item['title']}-{item['volume_number']}": item for item in existing_data}
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        current_year = datetime.now().year  # Adjust based on page context if needed
        
        for table in tables:
            # Extract month/year from preceding h1
            month_year = table.find_previous("h1").text.strip() if table.find_previous("h1") else f"{current_year}"
            year = re.search(r"\d{4}", month_year).group() if re.search(r"\d{4}", month_year) else current_year
            
            for row in table.find("tbody").find_all("tr"):
                cols = row.find_all("td")
                if len(cols) >= 5:
                    release_date = cols[0].text.strip()
                    title = cols[1].text.strip()
                    volume = cols[2].text.strip().replace("Volume ", "").replace("Vol. ", "")
                    purchase_link = cols[3].find("a")["href"]
                    publisher = cols[3].text.strip()
                    release_type = cols[4].text.strip()
                    
                    try:
                        date_obj = parse(f"{year} {release_date}", dayfirst=False)
                        formatted_date = date_obj.strftime("%Y-%m-%d")
                    except ValueError:
                        formatted_date = "Unknown"
                    
                    key = f"{title}-{volume}"
                    existing_entry = existing_dict.get(key, {})
                    collection = extract_collection(title, volume)
                    
                    entry = {
                        "title": title,
                        "volume_number": volume,
                        "release_date": formatted_date,
                        "publisher": publisher,
                        "book_link": purchase_link,
                        "release_type": release_type,
                        "collection": collection,
                        "last_updated": existing_entry.get("last_updated", datetime.utcnow().isoformat()),
                        "google_calendar_added": existing_entry.get("google_calendar_added", None)
                    }
                    
                    # Update last_updated only if data changed
                    if (existing_entry.get("release_date") != formatted_date or
                        existing_entry.get("publisher") != publisher or
                        existing_entry.get("release_type") != release_type or
                        existing_entry.get("book_link") != purchase_link):
                        entry["last_updated"] = datetime.utcnow().isoformat()
                    
                    tasks.append(fetch_metadata(session, purchase_link, volume))
                    releases.append(entry)
        
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