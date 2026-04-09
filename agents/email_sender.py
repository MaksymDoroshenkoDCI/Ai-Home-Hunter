"""Email sender for collected housing company contacts.

The script reads contacts from the `email_contacts` table with status
`not_sent`, composes a personalized message (using the template from the
user profile), sends it via SMTP, and updates the contact status to
`sent` (or `bounced` on failure).
"""

import logging
import smtplib
from email.message import EmailMessage
from datetime import datetime

from core.config import load_config
from core.database import init_db, EmailContact

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Email template – can be overridden in user_config.yaml under
# `email_template` if desired.
# ---------------------------------------------------------------------------
DEFAULT_SUBJECT = "Wohnungssuche – WBS 100 (1‑2‑Zimmer, 30‑50 m²)"
DEFAULT_BODY = """Sehr geehrte Damen und Herren,

mein Name ist {first_name} {last_name}, ich komme aus der Ukraine und befinde
mich derzeit in einer schwierigen Wohnsituation. Ich suche dringend eine
1‑2‑Zimmer‑Wohnung (30‑50 m²) mit einem Warmmietpreis bis 1 000 € und einem
Wohnberechtigungsschein (WBS 100).

Meine wichtigsten Daten:
- Anrede: {salutation}
- E‑Mail: {email}
- Telefon: {mobile_number}
- Aktuelle Adresse: {street} {street_number}, {zip_code} {city}
- Nettoeinkommen: {net_income} € / Monat
- Haushaltsgröße: {household_size}
- Keine Haustiere
- WBS‑Inhaber: {wbs_holder}

Ich würde mich sehr freuen, wenn Sie mir passende Angebote zusenden könnten
oder mich in Ihre Interessenten‑Datenbank aufnehmen würden.

Vielen Dank für Ihre Unterstützung.

Mit freundlichen Grüßen
{first_name} {last_name}
"""


def build_message(user_profile, recipient_email):
    msg = EmailMessage()
    msg["Subject"] = DEFAULT_SUBJECT
    msg["From"] = user_profile.email
    msg["To"] = recipient_email
    body = DEFAULT_BODY.format(
        first_name=user_profile.first_name,
        last_name=user_profile.last_name,
        salutation=user_profile.salutation or "",
        email=user_profile.email,
        mobile_number=user_profile.mobile_number or user_profile.phone,
        street=user_profile.street,
        street_number=user_profile.street_number,
        zip_code=user_profile.zip_code,
        city=user_profile.city,
        net_income=user_profile.net_income,
        household_size=user_profile.household_size,
        wbs_holder=user_profile.wbs_holder,
    )
    msg.set_content(body)
    return msg


def send_email(smtp_cfg, msg):
    try:
        with smtplib.SMTP_SSL(smtp_cfg["server"], smtp_cfg["port"]) as server:
            server.login(smtp_cfg["user"], smtp_cfg["password"])
            server.send_message(msg)
        return True
    except Exception as e:
        logger.error(f"SMTP send failed for {msg['To']}: {e}")
        return False


def run_sender():
    """Main entry point – iterate over unsent contacts and send the email.
    This function can be scheduled via APScheduler.
    """
    cfg = load_config()
    # Expect SMTP settings under cfg.email_smtp (add to user_config.yaml)
    smtp_cfg = getattr(cfg, "email_smtp", None)
    if not smtp_cfg:
        logger.error("SMTP configuration missing in user config.")
        return

    session = init_db()
    contacts = session.query(EmailContact).filter(EmailContact.status == "not_sent").all()
    if not contacts:
        logger.info("No unsent email contacts found.")
        session.close()
        return

    for contact in contacts:
        msg = build_message(cfg.user_profile, contact.email)
        success = send_email(smtp_cfg, msg)
        contact.status = "sent" if success else "bounced"
        contact.last_contacted = datetime.utcnow()
        session.add(contact)
        logger.info(f"Email to {contact.email} {'sent' if success else 'bounced'}.")

    session.commit()
    session.close()
    logger.info("Email sending run finished.")

if __name__ == "__main__":
    run_sender()
