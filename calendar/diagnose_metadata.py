import requests
from bs4 import BeautifulSoup
import json
import re
from collections import defaultdict
import time
import asyncio
from playwright.async_api import async_playwright

SAMPLES = {
    "Seven Seas": "https://sevenseasentertainment.com/books/theres-no-freaking-way-ill-be-your-lover-unless-light-novel-vol-6/",
    "J-Novel Club": "https://j-novel.club/series/nia-liston-the-merciless-maiden#volume-5",
    "Yen Press": "https://yenpress.com/titles/9781975392536-re-starting-life-in-another-world-short-story-collection-vol-2-light-novel"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://www.google.com/",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

async def fetch_seven_seas(url, retries=2):
    for attempt in range(retries + 1):
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
                page = await browser.new_page(extra_http_headers=HEADERS)
                await page.set_viewport_size({"width": 1280, "height": 720})
                
                print(f"Attempt {attempt + 1}/{retries + 1}: Navigating to {url}")
                response = await page.goto(url)
                await asyncio.sleep(8)
                await page.goto("https://sevenseasentertainment.com/")
                await asyncio.sleep(3)
                response = await page.goto(url)
                await asyncio.sleep(3)
                
                status = response.status if response else "Unknown"
                print(f"HTTP Status: {status}")
                if status >= 400:
                    raise Exception(f"Server returned status {status}")
                
                html = await page.content()
                await browser.close()
                return BeautifulSoup(html, "html.parser")
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt == retries:
                raise
            await asyncio.sleep(5)

def fetch_other(url):
    time.sleep(2)
    response = requests.get(url, headers=HEADERS, timeout=10)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")

def extract_metadata(url):
    data = defaultdict(list)
    
    try:
        if "sevenseas" in url:
            soup = asyncio.run(fetch_seven_seas(url))
        else:
            soup = fetch_other(url)

        if soup.find("meta", content=re.compile(r"sgcaptcha")):
            data["warning"].append("Captcha detected - limited data available")

        title_tag = soup.find("title")
        if title_tag:
            data["title"].append(title_tag.text.strip())

        desc_tag = soup.find("meta", {"name": "description"}) or soup.find("meta", {"property": "og:description"})
        if desc_tag and desc_tag.get("content") and "J-Novel Club is a digital publishing" not in desc_tag["content"]:
            data["description"].append(desc_tag["content"])

        if "sevenseas" in url:
            volume_meta = soup.find("div", id="volume-meta")
            if volume_meta:
                desc = volume_meta.find("p", class_=False)
                if desc:
                    data["description"].append(desc.text.strip())
                for b in volume_meta.find_all("b"):
                    key = b.text.strip().replace(":", "").lower().replace(" ", "_")
                    value = b.next_sibling.strip() if b.next_sibling else "N/A"
                    if key in {"price", "page_count", "isbn", "release_date", "early_digital"}:
                        data[key].append(value)
                creators = volume_meta.find_all("span", class_="creator")
                for creator in creators:
                    data["creators"].append(creator.text.strip())
                series_link = volume_meta.find("a", href=re.compile(r"/series/"))
                if series_link:
                    data["series"].append({
                        "name": series_link.text.strip(),
                        "url": series_link["href"]
                    })
            genre_block = soup.find("div", id="SSGL-block")
            if genre_block and genre_block.get("class") == ["age-rating"]:
                data["genres_themes"].append(genre_block.text.strip())
            age_block = soup.find("div", id="olderteen15")
            if age_block:
                data["age_rating"].append("Older Teen (15+)")
            else:
                data["age_rating"].append("Not listed")
            data["target_demographic"].append("Not listed")
            if "release_date" not in data:
                data["release_date"].append("Not listed")
            if "early_digital" not in data:
                data["early_digital"].append("Not listed")

        if "j-novel.club" in url:
            series_info = soup.find("div", class_="ffukg03")
            if series_info:
                desc = series_info.find_next("p")
                if desc:
                    data["description"].append(desc.text.strip())
            tags = soup.find_all("meta", {"property": "book:tag"})
            if tags:
                data["genres_themes"].extend([tag["content"] for tag in tags])
            creators = soup.find("meta", {"property": "book:author"})
            if creators:
                data["creators"].append(creators["content"].split('"')[1])
            data["age_rating"].append("Not listed")
            data["target_demographic"].append("Not listed")
            data["release_date"].append("Not listed")
            data["early_digital"].append("Not listed")

        if "yenpress" in url:
            details = soup.find("div", class_="detail-info")
            if details:
                for box in details.find_all("div", class_="detail-box"):
                    label = box.find(string=True, recursive=False)
                    if label:
                        key = label.strip().lower().replace(" ", "_")
                        value = box.find("p").text.strip() if box.find("p") else "N/A"
                        if key in {"price", "page_count", "isbn", "release_date"}:
                            data[key].append(value)
                        elif key == "":
                            for v in box.find("p").text.split("\n"):
                                if "pages" in v:
                                    data["page_count"].append(v.strip())
                                elif re.match(r"\d{10,13}", v):
                                    data["isbn"].append(v.strip())
                                elif re.match(r"[A-Za-z]{3} \d{1,2}, \d{4}", v):
                                    data["release_date"].append(v.strip())
                                elif "T (Teen)" in v or "Mature" in v:
                                    data["age_rating"].append(v.strip())
            desc_full = soup.find("div", class_="content-heading-txt")
            if desc_full:
                data["description"].append(desc_full.text.strip())
            labels = soup.find("div", class_="detail-labels")
            if labels:
                data["genres_themes"].extend([label.strip() for label in labels.text.split("\n") if label.strip()])
            if "age_rating" not in data:
                data["age_rating"].append("Not listed")
            data["target_demographic"].append("Not listed")
            if "release_date" not in data:
                data["release_date"].append("Not listed")
            if "early_digital" not in data:
                data["early_digital"].append("Not listed")

        return dict(data)
    except Exception as e:
        print(f"Error scraping {url}: {str(e)}")
        return {"error": str(e)}

if __name__ == "__main__":
    print("Starting metadata diagnosis")
    results = {publisher: extract_metadata(url) for publisher, url in SAMPLES.items()}
    
    with open("metadata_diagnosis.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("Diagnosis complete, saved to metadata_diagnosis.json")