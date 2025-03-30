import requests
from bs4 import BeautifulSoup
import json
import re

SAMPLES = {
    "Seven Seas": "https://sevenseasentertainment.com/books/theres-no-freaking-way-ill-be-your-lover-unless-light-novel-vol-6/",
    "J-Novel Club": "https://j-novel.club/series/nia-liston-the-merciless-maiden#volume-5",
    "Yen Press": "https://yenpress.com/titles/9781975392536-re-starting-life-in-another-world-short-story-collection-vol-2-light-novel"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def diagnose_page(url):
    print(f"Diagnosing {url}")
    try:
        response = requests.get(url, headers=HEADERS)
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

if __name__ == "__main__":
    print("Starting local diagnosis (no credentials required)")
    results = {publisher: diagnose_page(url) for publisher, url in SAMPLES.items()}
    
    with open("metadata_diagnosis.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Diagnosis complete, saved to metadata_diagnosis.json")