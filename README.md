# AI Home Hunter
Autonomous AI agent designed to revolutionize the apartment search and application process in Berlin.

## Features
- **Workflow A: Scouting & Scraping**: Monitors properties, filters based on config.
- **Workflow B: Application & Form Submission**: Auto-fills and applies with Playwright.
- **Workflow C: Email Monitoring**: Connects to Gmail, reads viewing invitations, uses a LLM to detect timeslots, and books them.

## Installation
1. Setup a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   playwright install
   ```
3. Configuration:
   - Copy `user_config.example.yaml` to `user_config.yaml`.
   - Update with your personal info, search criteria, and API keys.
4. Run:
   ```bash
   python main.py
   ```

## Architecture
- `main.py`: Entry point and scheduler using `apscheduler`.
- `core/`: Config and SQLite/SQLAlchemy database models.
- `agents/`: Independent workflows (Scraper, Application, EmailMonitor).
