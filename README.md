
```markdown
# 🏡 PropertyBot

A powerful web scraping project that gathers real estate listings from major Nigerian property websites and offers a user-friendly web interface to filter, preview, and export the data to CSV, Excel, or Google Sheets.

---

## 📸 Sample Output

### 🧾 Google Sheets Export
![Google Sheets Output](outputs/googlesheet_snapshot.PNG)

### 🌐 Web Interface
![Web App Interface](outputs/webapp.PNG)

---

## 📦 Features

- ✅ Scrapes property listings from:
  - NigeriaPropertyCentre.com
  - PropertyPro.ng
  - PrivateProperty.ng
- ✅ Collects key fields: title, price, city, category, agent contacts, image URL, and more
- ✅ Saves structured data to **MongoDB**
- ✅ Flask web interface to search and filter listings
- ✅ Export listings to:
  - **CSV**
  - **Excel**
  - **Google Sheets** (via OAuth)
- ✅ Optional: Automatically deduplicate listings
- ✅ Clean and organized codebase with logging and error handling

---

## 🗂 Project Structure

```

PropertyBot/
│
├── scrapers/                         # Main Playwright scraper scripts
│   ├── PROPERTYBOT\_SCRAPER\_1.py      # NigeriaPropertyCentre scraper
│   ├── PROPERTYBOT\_SCRAPER\_2.py      # PropertyPro.ng scraper
│   └── PROPERTYBOT\_SCRAPER\_3.py      # PrivateProperty.ng scraper
│
├── pipelines/                        # MongoDB pipelines and duplicate removal
│   ├── mongodb\_pipeline.py
│   └── remove\_duplicates\_script.py
│
├── middlewares/                      # Rotating user-agent support
│   └── user\_agent\_middleware.py
│
├── utils/                            # Google Sheets writer and helpers
│   ├── sheet\_writer.py
│   └── propertyAPIkeys.json          # 🔒 Google service account key (ignored by Git)
│
├── outputs/                          # Exported CSVs and snapshots (ignored)
│   ├── properties.csv
│   ├── googlesheet\_snapshot.PNG
│   └── webapp.PNG
│
├── WebApp/                           # Flask web interface for filtered export
│   ├── server.py                     # Main Flask app
│   ├── templates/
│   │   └── search.html
│   ├── static/
│   │   └── style.css
│   ├── .env                          # 🔒 Web app secrets
│   └── client\_secret.json            # 🔒 OAuth 2.0 credentials (ignored by Git)
│
├── .env                              # 🔒 Global environment secrets
├── README.md
└── requirements.txt

````

---

## 🚀 Getting Started

### 1. Install dependencies

```bash
pip install -r requirements.txt
playwright install
````

---

### 2. Set up environment variables

#### In your project root `.env` file:

```
FLASK_SECRET_KEY=your-flask-secret-key
GOOGLE_SERVICE_KEY=utils/propertyAPIkeys.json
```

#### In `WebApp/.env`:

```
CLIENT_SECRET_FILE=WebApp/client_secret.json
FLASK_SECRET_KEY=your-webapp-secret-key
```

---

### 3. Run a scraper

```bash
python -m scrapers.PROPERTYBOT_SCRAPER_1  # NGPC
python -m scrapers.PROPERTYBOT_SCRAPER_2  # PropertyPro.ng
python -m scrapers.PROPERTYBOT_SCRAPER_3  # PrivateProperty.ng
```

> Scraped data is saved into MongoDB (`PropertyBot.listings`).

---

### 4. Launch the web interface

```bash
cd WebApp
python server.py
```

> Visit [http://localhost:5000](http://localhost:5000) to filter, preview, and export property listings.

---

## 📤 Exporting to Google Sheets

Click **"Export to Google Sheets"** from the interface. You’ll be prompted to log in with your Google account.

* A new spreadsheet is created in your Drive
* Filtered listings are written with correct formatting
* OAuth credentials are **not hardcoded** — handled securely

---

## 🔐 Security Notes

This project is GitHub-safe.

### `.gitignore` already includes:

```
.env
**/.env
*.pyc
__pycache__/
outputs/
utils/propertyAPIkeys.json
WebApp/client_secret.json
```

> ✅ No sensitive files or secrets are committed.
> 🔒 Be sure to **create your own `.env` and credential files** before running.

---

## ✉️ Contact

**Author:** Abass Owolabi
📧 [abassowolabi091021@gmail.com](mailto:abassowolabi091021@gmail.com)

💼 Available for freelance scraping work on platforms like **Upwork**, **Fiverr**, **LinkedIn**, and more.

---

## 📝 License

This project is intended for **educational and personal use only**.
Please respect the [terms of service](https://en.wikipedia.org/wiki/Terms_of_service) of all websites being scraped.

```
