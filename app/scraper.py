import requests
from bs4 import BeautifulSoup

# 🌐 Utility to extract readable text from a page
def extract_section(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Remove scripts/styles
        for script in soup(["script", "style", "noscript"]):
            script.extract()

        # Extract and clean text
        text = soup.get_text(separator="\n", strip=True)
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n".join(lines)
    except Exception as e:
        print(f"Error fetching {url}:", e)
        return "Not available"

# 🔎 Each of these functions fetches a section
def fetch_menu():
    return extract_section("https://myoasisbar.co.uk/menu/")

def fetch_offers():
    return extract_section("https://myoasisbar.co.uk/events/")

def fetch_contact_info():
    return extract_section("https://myoasisbar.co.uk/contact/")

def fetch_faqs():
    return extract_section("https://myoasisbar.co.uk/faqs/")
