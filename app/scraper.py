import requests
from bs4 import BeautifulSoup

BASE_URL = "https://myoasisbar.co.uk"

headers = {
    "User-Agent": "Mozilla/5.0"
}

def fetch_menu():
    url = f"{BASE_URL}/menus"
    try:
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        items = []

        for section in soup.select(".menu-card"):
            title = section.select_one("h3, h4")
            for item in section.select("li"):
                name = item.text.strip()
                if name:
                    items.append({
                        "category": title.text.strip() if title else "Menu",
                        "name": name
                    })
        return items
    except Exception as e:
        return [{"error": f"Failed to fetch menu: {str(e)}"}]


def fetch_offers():
    url = f"{BASE_URL}/whats-on"
    try:
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        events = []

        for card in soup.select(".event-card, .elementor-post"):
            title = card.select_one("h2, h3, .elementor-post__title")
            date = card.select_one(".elementor-post__meta-data, .date")
            events.append({
                "title": title.text.strip() if title else "No title",
                "date": date.text.strip() if date else "No date"
            })
        return events
    except Exception as e:
        return [{"error": f"Failed to fetch events: {str(e)}"}]


def fetch_contact_info():
    url = f"{BASE_URL}/contact-us"
    try:
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        address = soup.select_one("address")
        phone = soup.select_one("a[href^='tel:']")
        email = soup.select_one("a[href^='mailto:']")
        hours = [li.text.strip() for li in soup.select("ul li") if any(day in li.text for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])]

        return {
            "address": address.text.strip() if address else None,
            "phone": phone.text.strip() if phone else None,
            "email": email.text.strip() if email else None,
            "hours": hours
        }
    except Exception as e:
        return {"error": f"Failed to fetch contact info: {str(e)}"}


def fetch_faqs():
    url = f"{BASE_URL}/faqs"
    try:
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        faqs = []
        for block in soup.select(".elementor-accordion-item"):
            question = block.select_one(".elementor-tab-title")
            answer = block.select_one(".elementor-tab-content")
            faqs.append({
                "question": question.text.strip() if question else "No question",
                "answer": answer.text.strip() if answer else "No answer"
            })

        return faqs
    except Exception as e:
        return [{"error": f"Failed to fetch FAQs: {str(e)}"}]
