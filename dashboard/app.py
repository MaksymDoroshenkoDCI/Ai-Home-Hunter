from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import logging

# Scheduler
from apscheduler.schedulers.background import BackgroundScheduler

# Import agents and config
from core.config import load_config
from core.database import init_db, Apartment
from agents.scraper import ScraperAgent
from agents.application import ApplicationAgent

logger = logging.getLogger("Dashboard")

app = FastAPI()

# Mount static files (CSS, JS)
app.mount("/static", StaticFiles(directory="dashboard/static"), name="static")

templates = Jinja2Templates(directory="dashboard/templates")

# Load configuration and DB session once
config = load_config()
session = init_db()

# Scheduler setup
from agents.email_collector import run_collector as email_collect
from agents.email_sender import run_sender as email_send

def scheduled_email_collect():
    try:
        email_collect()
        logger.info("Scheduled email collection completed")
    except Exception as e:
        logger.error(f"Scheduled email collection error: {e}")

def scheduled_email_send():
    try:
        email_send()
        logger.info("Scheduled email sending completed")
    except Exception as e:
        logger.error(f"Scheduled email sending error: {e}")

# Add email jobs to scheduler (run every 6 hours)
scheduler.add_job(scheduled_email_collect, 'interval', hours=6, id='email_collect_job')
scheduler.add_job(scheduled_email_send, 'interval', hours=6, id='email_send_job')


@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    # Render dashboard page
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/run_scraper")
async def run_scraper(background_tasks: BackgroundTasks):
    def task():
        try:
            scraper = ScraperAgent(config, session)
            scraper.run()
            logger.info("Scraper run completed via dashboard")
        except Exception as e:
            logger.error(f"Scraper error: {e}")
    background_tasks.add_task(task)
    return JSONResponse({"status": "started"})

@app.post("/run_application")
async def run_application(background_tasks: BackgroundTasks):
    def task():
        try:
            app_agent = ApplicationAgent(config, session)
            app_agent.run()
            logger.info("Application run completed via dashboard")
        except Exception as e:
            logger.error(f"Application error: {e}")
    background_tasks.add_task(task)
    return JSONResponse({"status": "started"})

@app.get("/stats")
async def stats():
    total_found = session.query(Apartment).filter(Apartment.status == "found").count()
    total_applied = session.query(Apartment).filter(Apartment.status == "applied").count()
    total_failed = session.query(Apartment).filter(Apartment.status == "failed_to_apply").count()
    return JSONResponse({
        "found": total_found,
        "applied": total_applied,
        "failed": total_failed
    })

@app.get("/apartments")
async def apartments():
    rows = session.query(Apartment).order_by(Apartment.found_at.desc()).limit(20).all()
    data = []
    for r in rows:
        data.append({
            "id": r.id,
            "address": r.address,
            "rent": r.warmmiete,
            "status": r.status,
            "url": r.url
        })
    return JSONResponse(data)
