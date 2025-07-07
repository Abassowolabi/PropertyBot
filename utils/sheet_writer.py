# -------------------------------- Google Sheets setup (unchanged) -------------------------------
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os


KEY_FILE = os.getenv("GOOGLE_SERVICE_KEY", "utils/propertyAPIkeys.json")
SHEET_NAME = "PropertyBotListings"

scope  = ["https://spreadsheets.google.com/feeds",
          "https://www.googleapis.com/auth/drive"]

if not os.path.exists(KEY_FILE):
    raise FileNotFoundError(f"❌ Google API key file not found at: {KEY_FILE}")


try:
    creds  = ServiceAccountCredentials.from_json_keyfile_name(KEY_FILE, scope)
    client = gspread.authorize(creds)
    sheet  = client.open(SHEET_NAME).sheet1
except Exception as e:
    raise RuntimeError(f"❌ Failed to authenticate with Google Sheets: {e}")


# -------------------------------- Listing helpers -----------------------------------------------
LISTING_HEADER = [
    "Website",  # ✅ Changed from "Source"
    "Category", "City", "Title",
    "Price (₦)", "Price (int)",
    "Location", "Bedrooms", "Bathrooms", "Toilets",
    "Agent Name", "Agent Phone", "Agent WhatsApp",
    "Image URL", "Listing URL"
]

existing_urls: set[str] = set()

def load_existing_urls(col: int = 15) -> None:
    """Fetch the URL column once and cache as `existing_urls`."""
    global existing_urls
    try:
        urls = sheet.col_values(col)
        existing_urls = set(urls[1:])      # skip header
    except Exception as e:
        print(f"⚠️  Error loading existing URLs: {e}")
        existing_urls = set()

def _ensure_min_rows(min_rows: int = 2) -> None:
    """Ensure the worksheet grid has at least `min_rows` rows."""
    current = sheet.row_count
    if current < min_rows:
        sheet.add_rows(min_rows - current)

def clear_sheet() -> None:
    """Clear everything below the header without shrinking the grid."""
    try:
        _ensure_min_rows(2)                      # ✅ Ensure at least 2 rows
        sheet.batch_clear(['A2:Z'])              # ✅ Clear below header
        sheet.update("A1", [LISTING_HEADER])
        print("🧹 Sheet cleared, header row reset.")
    except Exception as e:
        print(f"⚠️  Error clearing sheet: {e}")


def _dict_to_row(d: dict) -> list:
    return [
        d.get("website", ""),                   # ✅ Website is now the first column
        d.get("category", ""),
        d.get("city", ""),
        d.get("title", ""),
        d.get("price", ""),
        d.get("price_int", ""),
        d.get("location", ""),
        d.get("bedrooms", ""),
        d.get("bathrooms", ""),
        d.get("toilets", ""),
        d.get("agent_name", ""),
        d.get("phone", d.get("agent_call", "")),
        d.get("agent_whatsapp", ""),
        d.get("image_url", ""),
        d.get("url", "")
    ]

def clear_rows_by_website(website: str) -> None:
    try:
        all_rows = sheet.get_all_values()
        header = all_rows[0]
        rows = all_rows[1:]

        # Keep only rows not matching this website
        rows_to_keep = [row for row in rows if len(row) < 1 or row[0] != website]

        _ensure_min_rows(len(rows_to_keep) + 1)
        sheet.clear()
        sheet.update("A1", [header])
        if rows_to_keep:
            sheet.update("A2", rows_to_keep)
        print(f"🧹 Cleared rows for website '{website}', preserved others.")
    except Exception as e:
        print(f"⚠️  Error clearing by website: {e}")


def write_properties(listings: list[dict],
                     website: str,
                     clear_first: bool = True,
                     prepend: bool = True) -> None:
    """
    ▸ `listings` – list of property dicts.
    ▸ `website` – used to tag rows and clear only this website's rows.
    ▸ `clear_first` – if True, clear existing rows from this website.
    ▸ `prepend` – if True, insert new rows at top; else append bottom.
    """
    global existing_urls

    # ✅ Tag each listing with the website source
    for listing in listings:
        listing["website"] = website

    # ✅ Clear only this website's rows, or load for deduplication
    if clear_first:
        clear_rows_by_website(website)
        existing_urls = set()
    else:
        load_existing_urls()

    # ✅ Build new rows, skipping existing URLs
    new_rows: list[list] = []
    for listing in listings:
        url = listing.get("url", "")
        if url and url not in existing_urls:
            new_rows.append(_dict_to_row(listing))
            existing_urls.add(url)

    # ✅ Exit early if no new data
    if not new_rows:
        print(f"ℹ️  No new listings to add for '{website}'.")
        return

    # ✅ Insert new rows to the sheet
    try:
        if prepend:
            # Insert below header (row 2), newest at top
            sheet.insert_rows(list(reversed(new_rows)), row=2,
                              value_input_option="USER_ENTERED")
            print(f"✅ Inserted {len(new_rows)} new listings for '{website}' at the top.")
        else:
            # Append to bottom
            sheet.append_rows(new_rows, value_input_option="USER_ENTERED")
            print(f"✅ Appended {len(new_rows)} new listings for '{website}' at the bottom.")
    except Exception as e:
        print(f"❌ Error inserting rows for '{website}': {e}")
