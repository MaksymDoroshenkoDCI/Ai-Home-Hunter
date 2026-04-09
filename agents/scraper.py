import logging
import time
import re
from playwright.sync_api import sync_playwright
from core.config import AppConfig
from core.database import Apartment

logger = logging.getLogger("ScraperAgent")

class ScraperAgent:
    def __init__(self, config: AppConfig, session):
        self.config = config
        self.session = session
        self.base_url = "https://www.inberlinwohnen.de/wohnungsfinder/"

    def run(self):
        """
        Workflow A: Scouting & Scraping (Web Crawling)
        - Monitors inberlinwohnen.de (covers several municipal companies)
        - Parses listings
        - Filters by configuration criteria
        """
        logger.info("Running ScraperAgent workflow for InBerlinWohnen...")
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                )
                page = context.new_page()
                
                self.scrape_inberlinwohnen(page)
                
                browser.close()
        except Exception as e:
            logger.error(f"Error during scraping session: {e}", exc_info=True)

    def scrape_inberlinwohnen(self, page):
        logger.info(f"Navigating to {self.base_url}")
        page.goto(self.base_url, wait_until="networkidle")
        
        # Accept cookies if present
        try:
            cookie_button = page.get_by_role("button", name=re.compile("Alle akzeptieren|Accept all", re.IGNORECASE))
            if cookie_button.is_visible(timeout=5000):
                cookie_button.click()
                logger.info("Cookies accepted")
        except:
            pass

        # Apply basic filters from config
        logger.info("Applying filters from configuration...")
        try:
            # Click on 'Filter' button to open filter panel
            filter_btn = page.locator("button:has-text('Filter')")
            if filter_btn.is_visible():
                filter_btn.click()
                page.wait_for_timeout(1000)

            # Max Rent
            max_rent = self.config.search_criteria.max_warmmiete
            rent_input = page.locator("input[name='qmiete_max']")
            if rent_input.is_visible():
                rent_input.fill(str(max_rent))
            
            # Min Area
            min_area = self.config.search_criteria.min_area_sqm
            area_input = page.locator("input[name='qqm_min']")
            if area_input.is_visible():
                area_input.fill(str(min_area))

            # Apply / Search
            search_btn = page.locator("button:has-text('Suchen')")
            search_btn.click()
            page.wait_for_timeout(3000) # Wait for Livewire update
        except Exception as e:
            logger.warning(f"Could not apply some filters: {e}")

        # Switch to List View
        try:
            list_view_btn = page.locator("button[aria-label='Listenansicht']")
            if list_view_btn.is_visible():
                list_view_btn.click()
                page.wait_for_timeout(2000)
        except Exception as e:
            logger.warning(f"Could not switch to list view: {e}")

        # Parse listings
        listings = page.locator("button.list__item__title").all()
        logger.info(f"Found {len(listings)} listings on current page.")

        for listing in listings:
            try:
                # Extract summary info from header
                header_text = listing.inner_text()
                # Example: "2,0 Zimmer, 52,96 m2, 360,13 € | Gensweg 10, 12349 Neukölln"
                
                rooms_match = re.search(r"(\d+,\d+|\d+)\s*Zimmer", header_text)
                area_match = re.search(r"(\d+,\d+|\d+)\s*m2", header_text)
                rent_match = re.search(r"(\d+[\d\.,]*)\s*€", header_text)
                address_parts = header_text.split('|')
                address = address_parts[1].strip() if len(address_parts) > 1 else "Unknown"

                rooms = float(rooms_match.group(1).replace(',', '.')) if rooms_match else 0
                area = float(area_match.group(1).replace(',', '.')) if area_match else 0
                rent = float(rent_match.group(1).replace('.', '').replace(',', '.')) if rent_match else 0

                # Expand to get details and link
                listing.click()
                page.wait_for_timeout(1000)

                details_link_loc = page.locator("a[title='Zum Expose der Wohnungsbaugesellschaft']").first
                url = details_link_loc.get_attribute("href") if details_link_loc.is_visible() else None
                if url and not url.startswith('http'):
                    url = "https://www.inberlinwohnen.de" + url

                # WBS Check
                wbs_visible = page.locator("div:has-text('WBS:') + div").first.inner_text().lower() if page.locator("div:has-text('WBS:') + div").first.is_visible() else ""
                wbs_needed = "ja" in wbs_visible or "erforderlich" in wbs_visible
                
                # Check if we should skip due to WBS
                if wbs_needed and self.config.user_profile.wbs_holder.lower() == "no":
                    logger.info(f"Skipping {address} - WBS required but user has none.")
                    continue

                self.save_apartment(
                    address=address,
                    rent=rent,
                    area=area,
                    rooms=rooms,
                    url=url,
                    wbs_needed=wbs_needed
                )
                
                # Close expansion to avoid overlapping issues
                listing.click()

            except Exception as e:
                logger.error(f"Error parsing listing card: {e}")

    def save_apartment(self, address, rent, area, rooms, url, wbs_needed):
        if not url:
            return

        # Check if exists
        existing = self.session.query(Apartment).filter_by(url=url).first()
        if not existing:
            new_apt = Apartment(
                platform="inberlinwohnen",
                url=url,
                address=address,
                warmmiete=rent,
                area_sqm=area,
                rooms=rooms,
                wbs_required=wbs_needed,
                status='found'
            )
            self.session.add(new_apt)
            self.session.commit()
            logger.info(f"New apartment found and saved: {address} ({rent}€)")
        else:
            logger.debug(f"Apartment already in DB: {address}")

