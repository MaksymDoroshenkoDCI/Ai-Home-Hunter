import logging
from core.config import AppConfig
from core.database import Apartment
from playwright.sync_api import sync_playwright

logger = logging.getLogger("ApplicationAgent")

class ApplicationAgent:
    def __init__(self, config: AppConfig, session):
        self.config = config
        self.session = session
        # Mapping of config fields to possible form input identifiers (name, placeholder, label)
        self.field_map = {
            "first_name": ["first_name", "vorname", "First Name", "Vorname"],
            "last_name": ["last_name", "nachname", "Last Name", "Nachname"],
            "email": ["email", "e-mail", "E-Mail"],
            "phone": ["phone", "telefon", "Phone", "Telefon"],
            "net_income": ["net_income", "nettoeinkommen", "Net Income", "Nettoeinkommen"],
            "household_size": ["household_size", "haushaltsgröße", "Household Size", "Haushaltsgroesse"],
            "profession": ["profession", "beruf", "Profession", "Beruf"],
            "pets": ["pets", "haustiere", "Pets", "Haustiere"],
            "wbs_holder": ["wbs_holder", "wbs", "WBS"]
        }

    def run(self):
        """Workflow B: iterate over apartments with status 'found' and submit applications."""
        logger.info("Running ApplicationAgent workflow...")
        pending = self.session.query(Apartment).filter_by(status='found').all()
        if not pending:
            logger.info("No pending apartments to apply for.")
            return
        for apt in pending:
            try:
                success = self.submit_application(apt)
                apt.status = 'applied' if success else 'failed_to_apply'
                self.session.commit()
                logger.info(f"Apartment {apt.id} ({apt.address}) status set to {apt.status}")
            except Exception as e:
                logger.error(f"Error processing apartment {apt.id}: {e}", exc_info=True)
                apt.status = 'failed_to_apply'
                self.session.commit()

    def submit_application(self, apartment: Apartment) -> bool:
        """Open the apartment URL, locate the application form, fill it and submit.
        Returns True on successful submission, False otherwise.
        """
        logger.info(f"Submitting application for {apartment.url}")
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context()
                page = context.new_page()
                page.goto(apartment.url, wait_until="networkidle")
                # Find a button/link that opens the application form
                form_button = None
                for txt in ["Interesse bekunden", "Kontakt", "Anfrage senden", "Jetzt anfragen", "Bewerben"]:
                    btn = page.locator(f"button:has-text('{txt}')")
                    if btn.is_visible():
                        form_button = btn
                        break
                if not form_button:
                    for txt in ["Interesse bekunden", "Kontakt", "Anfrage senden", "Jetzt anfragen", "Bewerben"]:
                        lnk = page.locator(f"a:has-text('{txt}')")
                        if lnk.is_visible():
                            form_button = lnk
                            break
                if not form_button:
                    logger.warning("Application button not found on page")
                    return False
                form_button.click()
                page.wait_for_timeout(1500)
                # Fill form fields using the field_map and user profile data
                user = self.config.user_profile
                for attr, candidates in self.field_map.items():
                    value = getattr(user, attr, None)
                    if value is None:
                        continue
                    field = None
                    for cand in candidates:
                        # Try by name attribute
                        field = page.locator(f"input[name='{cand}']")
                        if field.is_visible():
                            break
                        # Try by placeholder (contains)
                        field = page.locator(f"input[placeholder*='{cand}']")
                        if field.is_visible():
                            break
                        # Try by label text then sibling input
                        field = page.locator(f"label:has-text('{cand}') >> .. >> input")
                        if field.is_visible():
                            break
                    if field and field.is_visible():
                        field.fill(str(value))
                    else:
                        logger.debug(f"Could not locate field for {attr} (candidates: {candidates})")
                # Submit the form
                submit_btn = page.locator("button[type='submit']")
                if not submit_btn.is_visible():
                    submit_btn = page.locator("button:has-text('Absenden')")
                if not submit_btn.is_visible():
                    submit_btn = page.locator("button:has-text('Senden')")
                if submit_btn.is_visible():
                    submit_btn.click()
                    page.wait_for_timeout(2000)
                    logger.info("Form submitted successfully")
                    return True
                else:
                    logger.warning("Submit button not found")
                    return False
        except Exception as e:
            logger.error(f"Exception during application submission: {e}", exc_info=True)
            return False
