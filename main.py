import logging
from apscheduler.schedulers.background import BlockingScheduler
from core.config import load_config
from core.database import init_db
from agents.scraper import ScraperAgent
from agents.application import ApplicationAgent
from agents.email_monitor import EmailMonitorAgent

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AIHomeHunter")

def setup_workflows():
    try:
        config = load_config()
        logger.info("Configuration loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return

    # Initialize Database
    try:
        session = init_db()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return

    # Initialize agents
    scraper = ScraperAgent(config, session)
    application_agent = ApplicationAgent(config, session)
    email_monitor = EmailMonitorAgent(config, session)

    scheduler = BlockingScheduler()
    
    # Workflow A: Scouting & Scraping (Run every 15 minutes)
    scheduler.add_job(scraper.run, 'interval', minutes=15, id='scraping_job')
    
    # Workflow B: Application Submission (Triggered by scraper or run periodically)
    scheduler.add_job(application_agent.run, 'interval', minutes=15, id='application_job')

    # Workflow C: Email Monitoring & Auto-Response (Run every 2 minutes)
    scheduler.add_job(email_monitor.run, 'interval', minutes=2, id='email_job')
    
    logger.info("Starting AI Home Hunter scheduler...")
    logger.info("Press Ctrl+C to exit")
    
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Stopping AI Home Hunter.")

if __name__ == "__main__":
    setup_workflows()
