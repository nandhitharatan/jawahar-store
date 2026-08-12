# Jawahar Enterprises - Store Management App

Desktop retail management application for Jawahar Enterprises built with Python Flask and Electron.

## Project Structure

```
jawahar-store/
├── backend/            # Python Flask Backend API & SQLite Database
│   ├── app.py          # Application Factory
│   ├── database.py     # SQLAlchemy DB Instance
│   ├── models.py       # Database Schema Models
│   ├── routes.py       # API Endpoints & Page Routes
│   ├── helpers.py      # Business Logic & Utility Functions
│   ├── migrate.py      # Schema Migration Script
│   ├── run.py          # Server Entry Point (Port 5000)
│   ├── requirements.txt# Python Dependencies
│   └── store.db        # SQLite Database File
│
└── frontend/           # Electron Shell, Templates & Assets
    ├── main.js         # Electron Main Process (Launches Backend)
    ├── loading.html    # App Loading Screen
    ├── package.json    # Electron & Build Dependencies
    ├── templates/      # Jinja2 HTML Templates
    └── static/         # CSS Styles, Product Images & Uploads
```

## Running the Application

### Option 1: Electron Desktop App (Recommended)
1. Navigate to the `frontend` folder:
   ```bash
   cd frontend
   ```
2. Start the application:
   ```bash
   npm start
   ```

### Option 2: Python Backend Only (Web Mode)
1. Navigate to the `backend` folder:
   ```bash
   cd backend
   ```
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the Flask development server:
   ```bash
   python run.py
   ```
4. Open `http://127.0.0.1:5000` in your web browser.
