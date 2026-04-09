"""Email collector for small Berlin housing companies.

The script fetches the main website of each company, tries to locate a
"Impressum" or "Kontakt" page, extracts e‑mail addresses using a regular
expression and stores them in the `email_contacts` table.

It is intended to be run as a background job (APScheduler) but can also be
executed manually.
"""

import re
import logging
from urllib.parse import urljoin
from typing import List, Tuple

import requests
from bs4 import BeautifulSoup

from core.database import init_db, EmailContact

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration – list of companies (name, base URL)
# ---------------------------------------------------------------------------
COMPANIES: List[Tuple[str, str]] = [
    ("Berlinraum GmbH", "https://www.berlinraum.de"),
    ("Immomexxt GmbH", "https://www.immomexxt.de"),
    ("bwv-berlin.de", "https://www.bwv-berlin.de"),
    ("gewobau-berlin.de", "https://www.gewobau-berlin.de"),
    ("hws-berlin.de", "https://www.hws-berlin.de"),
    ("core-berlin.de", "https://www.core-berlin.de"),
    ("taekker.de", "https://www.taekker.de"),
    ("evmc.de", "https://www.evmc.de"),
    # add more as needed
]

EMAIL_REGEX = re.compile(r"[\w.%+-]+@[\w.-]+\.[a-zA-Z]{2,}")


def fetch_page(url: str) -> str:
    """Return page HTML or empty string on failure."""
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        logger.warning(f"Failed to fetch {url}: {e}")
        return ""


def find_contact_page(base_url: str) -> str:
    """Try common contact page paths and return the first successful URL.
    If none succeed, return the base URL.
    """
    candidates = ["/impressum", "/kontakt", "/contact", "/about"]
    for path in candidates:
        candidate_url = urljoin(base_url, path)
        html = fetch_page(candidate_url)
        if html:
            return candidate_url
    # fallback – just the base URL
    return base_url


def extract_emails(html: str) -> List[str]:
    """Parse HTML and return a list of unique e‑mail addresses."""
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator=" ")
    emails = set(EMAIL_REGEX.findall(text))
    return list(emails)


def store_emails(session, company_name: str, website: str, emails: List[str]):
    """Insert new EmailContact rows; ignore duplicates.
    Existing rows are left untouched – only the `last_contacted` field may be
    updated later by the sender script.
    """
    for email in emails:
        existing = session.query(EmailContact).filter_by(email=email).first()
        if existing:
            continue
        contact = EmailContact(
            company_name=company_name,
            email=email,
            website=website,
            status="not_sent",
        )
        session.add(contact)
        logger.info(f"Added email contact {email} for {company_name}")
    session.commit()


def run_collector():
    """Main entry point – iterate over COMPANIES, collect e‑mails and store.
    This function is scheduled by APScheduler.
    """
    session = init_db()
    for name, base_url in COMPANIES:
        contact_url = find_contact_page(base_url)
        html = fetch_page(contact_url)
        if not html:
            continue
        emails = extract_emails(html)
        if emails:
            store_emails(session, name, base_url, emails)
    session.close()
    logger.info("Email collection finished")

if __name__ == "__main__":
    run_collector()
