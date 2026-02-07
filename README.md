# car_rental

## Project description
Simple Flask + SQLite app that automates a commercial car rental office. It tracks
cars, customers, issued rentals, and computes pricing with year-based adjustments,
rental-period discounts, loyalty discounts, and penalties for poor return condition.

## Project structure
- app.py - entry point that creates and runs the Flask app.
- rental_app/ - application modules (db, pricing, routes, app factory).
- templates/ - HTML pages for the dashboard, cars, customers, and rentals.
- static/ - CSS and JavaScript assets.
- requirements.txt - Python dependencies.
- car_rental.db - SQLite database (created on first run).

## How to launch
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000` in the browser.

## Technologies
- Python
- Flask
- SQLite
- HTML/CSS/JavaScript
