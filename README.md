# 👗 Jawahar Enterprises – Store Management App

A modern, high-performance **Desktop Retail & Store Management Application** built for **Jawahar Enterprises** (Women's Apparel Store). Featuring an **Electron** desktop interface, **Python Flask REST API**, **SQLAlchemy ORM**, and **SQLite** database storage.

---

## 🌟 Key Features

- 📊 **Dashboard & Analytics**: Real-time tracking of daily revenue, total orders, active inventory count, low-stock warnings, and recent transaction history.
- 💳 **Billing & POS System**: Fast checkout interface supporting search, category filtering, per-size stock validation, custom percentage discounts, automatic GST calculation (18% default), and print-ready receipt generation.
- 👗 **Product Catalog Management**: Manage apparel inventory across categories (Kurtis, Sarees, Lehengas, Gowns, Suit Sets, Bottoms, Dupattas, etc.) with product image uploads and size management.
- 📏 **Per-Product Custom Size Charts**:
  - Configure custom body and length measurements per product (Bust, Waist, Hips, Across Shoulder, Kurta Length, Inseam, etc.).
  - Category auto-presets for rapid setup (Kurtis, Palazzo, Gowns, Leggings, Skirts, Blouses, Dupattas).
  - Custom size support (Standard XS–XXL, Free Size, and custom numeric sizes like 28, 30, 32).
  - Dynamic **Inches ↔ Centimeters (cm)** measurement conversion.
- 📦 **Per-Size Inventory Control**: Inline stock quantity updates, automatic deduction upon sales transactions, and threshold alerts for low-stock items.
- 📈 **Sales Reporting**: Comprehensive revenue reporting over custom date ranges, payment method breakdown (Cash, Card, UPI), and top-selling product metrics.
- ⚙️ **Store Settings**: Customizable store details (Store Name, GSTIN Number, Phone, Email, Address, Currency Symbol `₹`, GST Rate %, Low Stock Threshold).

---

## 📂 Project Structure

```
jawahar-store/
├── backend/                  # Python Flask Backend API & Database
│   ├── app.py                # Application Factory & Configuration
│   ├── database.py           # SQLAlchemy Database Instance
│   ├── models.py             # Database Models (Product, ProductSizeChart, Transaction, etc.)
│   ├── routes.py             # REST API Endpoints & HTML Page Routes
│   ├── helpers.py            # Sales Logic, Invoice Generators & Reports
│   ├── migrate.py            # SQLite Database Schema Migration Utility
│   ├── run.py                # Flask Dev Server Entry Point (Port 5000)
│   ├── requirements.txt      # Python Dependencies
│   └── store.db              # SQLite Database File
│
├── frontend/                 # Desktop GUI Shell, Templates & Assets
│   ├── main.js               # Electron Main Process (Launches Backend Server)
│   ├── loading.html          # Application Splash Screen
│   ├── package.json          # Node & Electron Dependencies
│   ├── static/               # Styling Assets & Image Uploads
│   │   ├── css/              # Main CSS Stylesheet
│   │   ├── images/           # Application Icons & Product Uploads
│   │   └── uploads/          # User-uploaded files
│   └── templates/            # Jinja2 Dynamic HTML Templates
│       ├── base.html         # Master Base Layout & Sidebar Navigation
│       ├── billing.html      # Point of Sale & Checkout Screen
│       ├── dashboard.html    # Analytics Dashboard Page
│       ├── inventory.html    # Stock Management Page
│       ├── products.html     # Product Catalog & Size Chart Setup
│       ├── product_size_chart.html # Standalone Product Size Chart Editor
│       ├── sales_report.html # Revenue & Sales Reports
│       └── settings.html     # Store Configuration Page
│
└── README.md                 # Project Overview & Setup Instructions
```

---

## 💻 Tech Stack

- **Desktop Shell**: Electron 28 (`electron`, `electron-builder`)
- **Backend Framework**: Python 3, Flask 3.1
- **Database & ORM**: SQLite 3, Flask-SQLAlchemy 3.1, SQLAlchemy 2.0
- **Frontend / Templating**: HTML5, Vanilla CSS3, JavaScript (ES6+), Jinja2

---

## 🚀 How to Run

### Option 1: Electron Desktop App (Recommended)

1. Navigate to the `frontend` folder:
   ```bash
   cd frontend
   ```

2. Install Node dependencies (if running for the first time):
   ```bash
   npm install
   ```

3. Launch the desktop application:
   ```bash
   npm start
   ```

---

### Option 2: Python Backend Only (Web Mode)

1. Navigate to the `backend` folder:
   ```bash
   cd backend
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Start the Flask server:
   ```bash
   python run.py
   ```

4. Open your web browser and navigate to:
   ```
   http://127.0.0.1:5000
   ```

---

## 📦 Building Executable (.exe)

To build a standalone Windows executable:

```bash
cd frontend
npm run build-win
```

The output installer/exe will be generated in `frontend/dist/`.
