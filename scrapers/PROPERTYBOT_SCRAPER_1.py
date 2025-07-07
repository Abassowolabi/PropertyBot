import time
import random
import logging
import os
import sys
from pprint import pformat
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
from typing import Optional
from datetime import datetime
from pipelines.mongodb_pipeline import MongoPipeline
from middlewares.user_agent_middleware import RotatingUserAgentMiddleware
from utils.sheet_writer import write_properties  # REDACTED version assumed

# ---------------------------- Windows Logging Fix ----------------------------
if os.name == "nt":
    try:
        import ctypes
        ctypes.windll.kernel32.SetConsoleOutputCP(65001)
    except Exception:
        pass

# ---------------------------- Logging Setup ----------------------------
logger = logging.getLogger()
logger.setLevel(logging.INFO)
if logger.hasHandlers():
    logger.handlers.clear()

file_handler = logging.FileHandler("scraper.log", mode="a", encoding="utf-8")
file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger.addHandler(file_handler)

console_handler = logging.StreamHandler(stream=sys.stdout)
console_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger.addHandler(console_handler)

# ---------------------------- Config ----------------------------
cities = ["city-1", "city-2"]
BASE_URL = "https://example-property-site.com/property-for-sale/{}"
USER_AGENTS = [
    "Mozilla/5.0 ... Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 ... Chrome/125.0.0.0 Safari/537.36"
]
STATE_FILE = "state.json"
STATIC_UA = random.choice(USER_AGENTS)

# ---------------------------- Helpers ----------------------------

def safe_inner_text(elem, default="N/A"):
    try:
        return elem.inner_text().strip() if elem else default
    except:
        return default

def safe_get_attribute(elem, attr, default="N/A"):
    try:
        return elem.get_attribute(attr) if elem else default
    except:
        return default

def extract_or_na(benefit_list, index):
    try:
        text = safe_inner_text(benefit_list[index])
        return text if text and text != "0" else "N/A"
    except:
        return "N/A"

def extract_category_from_details(page) -> str:
    # REDACTED: Specific logic for extracting category from page DOM
    return "N/A"

# ---------------------------- Scraping Function ----------------------------

def scrape_city(page, city, pipeline):
    city_url = BASE_URL.format(city)

    try:
        page.goto(city_url, timeout=60000)
        time.sleep(3)
    except Exception as e:
        logging.error(f"❌ Failed to load {city}: {e}")
        return []

    listings_data = []
    max_pages = 2  # Reduced for public demo
    page_count = 0

    while True:
        page_count += 1
        if page_count > max_pages:
            logging.info("🛑 Max page limit reached.")
            break

        try:
            page.wait_for_selector("div.result-listings", timeout=30000)
            listings = page.query_selector_all("div.listing")  # simplified selector
        except Exception as e:
            logging.error(f"❌ Error loading listings: {e}")
            break

        detail_links = []
        for listing in listings:
            link_elem = listing.query_selector("h2 > a")
            relative_url = safe_get_attribute(link_elem, "href", None)
            if relative_url:
                detail_links.append(f"https://example-property-site.com{relative_url}")

        for full_url in detail_links:
            try:
                page.goto(full_url)
                time.sleep(2)

                # REDACTED: Full data extraction logic
                # Title, Location, Price, Category, Agent, Image, Contact

                listing_data = {
                    "website": "example-property-site.com",
                    "city": city,
                    "title": "REDACTED",
                    "price": "REDACTED",
                    "price_int": 0,
                    "location": "REDACTED",
                    "bedrooms": "N/A",
                    "bathrooms": "N/A",
                    "toilets": "N/A",
                    "agent_name": "REDACTED",
                    "agent_whatsapp": "REDACTED",
                    "agent_call": "REDACTED",
                    "image_url": "https://example.com/image.jpg",
                    "url": full_url,
                    "category": "REDACTED",
                    "date_scraped": datetime.utcnow()
                }

                pipeline.process_item(listing_data)
                listings_data.append(listing_data)
                logging.info(pformat(listing_data, sort_dicts=False))

            except Exception as e:
                logging.error(f"❌ Error scraping a listing: {e}")

            page.go_back()
            page.wait_for_selector("div.listing", timeout=30000)
            time.sleep(random.uniform(2, 3))

        # REDACTED: Pagination logic
        break  # End loop early for demo

    return listings_data

# ---------------------------- Main ----------------------------

def main():
    pipeline = MongoPipeline()
    pipeline.open()

    middleware = RotatingUserAgentMiddleware()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        total_scraped = 0
        all_listings = []

        for city in cities:
            context = browser.new_context(
                locale="en-US",
                timezone_id="Africa/Lagos",
                viewport={"width": 1280, "height": 800},
                storage_state=STATE_FILE if os.path.exists(STATE_FILE) else None,
            )
            context.route("**/*", middleware)
            page = context.new_page()
            stealth_sync(page)

            listings = scrape_city(page, city, pipeline)
            all_listings.extend(listings)
            total_scraped += len(listings)
            context.close()

        write_properties(all_listings, website="example-property-site.com", clear_first=True, prepend=True)
        browser.close()

    pipeline.close()
    logging.info(f"\n✅ Scraping complete. Total listings scraped: {total_scraped}")


if __name__ == "__main__":
    main()
