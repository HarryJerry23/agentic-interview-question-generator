"""Web scraping utility — extract text content from URLs."""

import requests
from bs4 import BeautifulSoup


def scrape_url(url: str) -> str | None:
    """Fetch a URL and extract clean text content."""
    try:
        resp = requests.get(url, timeout=15, headers={
            "User-Agent": "Mozilla/5.0 (Educational Research Bot)"
        })
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        return text[:6000]
    except Exception:
        return None
