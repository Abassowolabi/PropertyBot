import time
import re
import logging
from pprint import pformat
from datetime import datetime
from playwright.sync_api import sync_playwright
from pipelines.mongodb_pipeline import MongoPipeline
from middlewares.user_agent_middleware import RotatingUserAgentMiddleware
from utils.sheet_writer import write_properties
import sys
import os
import random

# -- Logging setup (UTF-8 compatible) --
if os.name == "nt":
    try:
        import ctypes
        ctypes.windll.kernel32.SetConsoleOutputCP(65001)
    except Exception:
        pass

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

# -- Helpers --
def safe_inner_text(element, default="N/A"):
    try:
        return element.inner_text().replace("\xa0", " ").strip() if element else default
    except:
        return default

def safe_get_attribute(element, attr, default="N/A"):
    try:
        return element.get_attribute(attr) if element else default
    except:
        return default

def normalize_zero_to_na(value):
    return "N/A" if value == "0" else value

# -- Core Scraper --
def scrape_location(page, city_url, city_name, pipeline, listings, max_pages=3, category="N/A"):
    try:
        page.goto(city_url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_selector("div.property-listing", timeout=15000)
    except Exception as e:
        logging.error(f"Failed to load {city_url}: {e}")
        return

    for page_num in range(max_pages):
        logging.info(f"📄 Scraping {city_name.title()} - {category.title()} - Page {page_num + 1}...")

        try:
            listings_on_page = page.query_selector_all("div.property-listing")
        except Exception as e:
            logging.error(f"Error selecting listings: {e}")
            break

        if not listings_on_page:
            logging.warning("⚠️ No listings found.")
            break

        for listing in listings_on_page:
            try:
                title = safe_inner_text(listing.query_selector("h4"))
                price = safe_inner_text(listing.query_selector("span.price"))
                location = safe_inner_text(listing.query_selector("address"))
                full_url = "https://example.com/fake-url"
                image_url = "https://example.com/image.jpg"

                listing_data = {
                    "website": "example.com",
                    "city": city_name,
                    "category": category,
                    "title": title,
                    "price": price,
                    "price_int": 0,
                    "location": location,
                    "bedrooms": "N/A",
                    "bathrooms": "N/A",
                    "toilets": "N/A",
                    "agent_name": "REDACTED",
                    "phone": "REDACTED",
                    "image_url": image_url,
                    "url": full_url,
                    "date_scraped": datetime.utcnow()
                }

                pipeline.process_item(listing_data)
                listings.append(listing_data)
                logging.info(pformat(listing_data, sort_dicts=False))

                time.sleep(random.uniform(0.5, 1.2))  # throttle
            except Exception as e:
                logging.error(f"❌ Listing error: {e}")

        try:
            next_button = page.query_selector("a.next-page")
            if next_button:
                next_button.click()
                page.wait_for_load_state("domcontentloaded", timeout=10000)
                time.sleep(2)
            else:
                break
        except Exception as e:
            logging.warning(f"Pagination failed: {e}")
            break

# -- Main loop over cities/categories --
def scrape_cities(categories, cities, pipeline, listings, max_pages=3):
    with sync_playwright() as p:
        for category in categories:
            for city in cities:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context()

                # Route filtering (ads, trackers, unwanted domains)
                def block_routes(route, request):
                    if any(k in request.url for k in ["ads", "criteo", "utm_", "tracking"]):
                        return route.abort()
                    return route.continue_()

                context.route("**/*", block_routes)
                context.route("**/*", RotatingUserAgentMiddleware())

                page = context.new_page()
                city_url = f"https://example.com/for-sale/{category}/{city}"
                scrape_location(page, city_url, city, pipeline, listings, max_pages, category)

                page.close()
                context.close()
                browser.close()

# -- Entry point --
if __name__ == "__main__":
    cities_to_scrape = ["lagos", "abuja"]
    categories_to_scrape = ["houses", "land", "commercial", "flats-apartments"]

    pipeline = MongoPipeline()
    pipeline.open()

    listings = []
    scrape_cities(categories_to_scrape, cities_to_scrape, pipeline, listings, max_pages=3)

    pipeline.close()
    logging.info("✅ Scraping complete.")
    write_properties(listings, website="example.com", clear_first=True, prepend=True)
