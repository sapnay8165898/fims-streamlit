# File Integrity Monitoring System (FIMS)

A Streamlit-based security tool that detects unauthorized file changes using SHA-256 hashing.

## Features
- Baseline creation with SHA-256 / SHA-1 / MD5 / SHA-512
- Change detection: Modified / Added / Deleted / Permission changes
- Real-time monitoring via watchdog
- Interactive dashboard (Streamlit + Plotly)
- Change log with CSV export
- Analytics: charts of changes by type and over time

## Tech Stack
Python 3.9, Streamlit, Watchdog, Plotly, Pandas

## How to Run
1. Install dependencies: `pip install -r requirements.txt`
2. Launch: `streamlit run app.py`
3. Open http://localhost:8501

## Usage
1. Enter a target directory in the sidebar
2. Click **Create Baseline** to snapshot the current state
3. Edit / add / delete files in the target directory
4. Click **Scan Now** to detect changes
5. Optional: **Start Real-Time Watch** for live monitoring

## Project Structure
- `app.py` — Streamlit dashboard
- `modules/hasher.py` — File hashing engine
- `modules/baseline.py` — Baseline storage & diffing
- `modules/alerts.py` — Change logging
- `modules/watcher.py` — Real-time watchdog observer
- `modules/utils.py` — Helpers

## Screenshots
See `screenshots/` folder.

## Author
