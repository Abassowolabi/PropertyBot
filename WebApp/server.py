from flask import Flask, render_template, request, send_file, session, redirect, url_for
from datetime import datetime, timedelta, timezone
from pymongo import MongoClient
from dotenv import load_dotenv
from io import BytesIO, StringIO
import pandas as pd
import os
import json

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

load_dotenv()

CLIENT_SECRET_FILE = os.getenv("CLIENT_SECRET_FILE", "client_secret.json")

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.getenv("FLASK_SECRET_KEY", "fallback-insecure-dev-key")

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
db = client["PropertyBot"]
collection = db["listings"]

# Google Sheets scopes
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive.file"]


# ----------------------------- Helpers -----------------------------
def get_scraped_after_from_range(range_value):
    now = datetime.now(timezone.utc)
    if range_value == "today":
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif range_value == "this_week":
        return now - timedelta(days=now.weekday())
    elif range_value == "last_7_days":
        return now - timedelta(days=7)
    elif range_value == "this_month":
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif range_value == "since_january":
        return datetime(now.year, 1, 1, tzinfo=timezone.utc)
    return None


def build_query_from_filters(args):
    query = {}

    # Use manual type conversion with defaults
    try:
        price_min = int(args.get("price_min", ""))
    except (ValueError, TypeError):
        price_min = None

    try:
        price_max = int(args.get("price_max", ""))
    except (ValueError, TypeError):
        price_max = None

    city = args.get("city")
    category = args.get("category")
    scraped_after_range = args.get("scraped_after_range")

    if price_min is not None:
        query["price_int"] = {"$gte": price_min}
    if price_max is not None:
        query.setdefault("price_int", {})["$lte"] = price_max
    if city:
        query["city"] = {"$regex": f"^{city}$", "$options": "i"}
    if category:
        query["category"] = {"$regex": f"^{category}$", "$options": "i"}

    scraped_after = get_scraped_after_from_range(scraped_after_range)
    if scraped_after:
        query["date_scraped"] = {"$gte": scraped_after}

    return query


def listings_to_dataframe(listings):
    for l in listings:
        l["_id"] = str(l["_id"])
    return pd.DataFrame(listings)


# ----------------------------- Routes -----------------------------
@app.route("/")
def home():
    page = max(request.args.get("page", 1, type=int), 1)
    per_page = 100
    query = build_query_from_filters(request.args)

    total_count = collection.count_documents(query)
    total_pages = (total_count + per_page - 1) // per_page
    skip = (page - 1) * per_page

    listings = list(collection.find(query).skip(skip).limit(per_page).sort("price_int", 1))

    return render_template("search.html",
                           listings=listings,
                           page=page,
                           total_pages=total_pages,
                           filters=request.args)


@app.route("/download")
def download():
    file_format = request.args.get("format", default="csv")
    query = build_query_from_filters(request.args)
    listings = list(collection.find(query))

    if not listings:
        return "No data available for export."

    df = listings_to_dataframe(listings)
    now_str = datetime.now().strftime("%Y-%m-%d_%H-%M")

    if file_format == "excel":
        output = BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)
        return send_file(output,
                         download_name=f"property_data_{now_str}.xlsx",
                         as_attachment=True,
                         mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    elif file_format == "sheets":
        session["filters"] = request.args.to_dict()
        return redirect(url_for("authorize_google"))

    else:
        output = StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        return send_file(BytesIO(output.getvalue().encode()),
                         download_name=f"property_data_{now_str}.csv",
                         as_attachment=True,
                         mimetype="text/csv")


# ----------------------------- Google OAuth -----------------------------
@app.route("/authorize")
def authorize_google():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRET_FILE,
        scopes=SCOPES,
        redirect_uri=url_for("oauth2callback", _external=True),
    )
    auth_url, _ = flow.authorization_url(prompt="consent", include_granted_scopes="true")
    return redirect(auth_url)


@app.route("/oauth2callback")
def oauth2callback():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRET_FILE,
        scopes=SCOPES,
        redirect_uri=url_for("oauth2callback", _external=True),
    )
    flow.fetch_token(authorization_response=request.url)

    credentials = flow.credentials
    session["credentials"] = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes
    }
    return redirect(url_for("export_to_sheets"))


@app.route("/export-to-sheets")
def export_to_sheets():
    if "credentials" not in session:
        return redirect(url_for("authorize_google"))

    creds = Credentials(**session["credentials"])
    service = build("sheets", "v4", credentials=creds)

    filters = session.get("filters", {})
    query = build_query_from_filters(filters)
    listings = list(collection.find(query))

    if not listings:
        return "No listings matched your filters."

    df = listings_to_dataframe(listings)

    df = df.fillna("")


    # Convert all datetime-like columns to string to avoid serialization error
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].astype(str)

    values = [df.columns.tolist()] + df.values.tolist()


    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    spreadsheet = service.spreadsheets().create(
        body={
            "properties": {
                "title": f"Property Listings {now_str}"
            }
        }
    ).execute()

    sheet_id = spreadsheet["spreadsheetId"]
    service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range="Sheet1!A1",
        valueInputOption="RAW",
        body={"values": values}
    ).execute()

    sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}"
    return redirect(sheet_url)


if __name__ == "__main__":
    app.run(debug=True)
