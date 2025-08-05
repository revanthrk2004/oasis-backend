import requests
from bs4 import BeautifulSoup

BASE = "https://myoasisbar.co.uk"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def clean_text(soup):
    for el in soup(["script", "style", "noscript"]):
        el.extract()
    return "\n".join([line.strip() for line in soup.get_text(separator="\n", strip=True).splitlines() if line.strip()])

def fetch_page(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        return clean_text(soup)
    except Exception as e:
        print(f"Error fetching {url}:", e)
        return "Not available"

def fetch_menu():
    return fetch_page(f"{BASE}/menu")

def fetch_events():
    return fetch_page(f"{BASE}/whats-on")

def fetch_private_hire():
    return fetch_page(f"{BASE}/private-hire-parties")

def fetch_about():
    return fetch_page(f"{BASE}/about-us")

def fetch_partners():
    return fetch_page(f"{BASE}/partners")

def fetch_faqs():
    return fetch_page(f"{BASE}/faqs")

def fetch_contact_info():
    return fetch_page(f"{BASE}/contact-us")
