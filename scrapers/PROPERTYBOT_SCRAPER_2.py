import re
import time
import logging
from pprint import pformat
from datetime import datetime
from playwright.sync_api import sync_playwright
from pipelines.mongodb_pipeline import MongoPipeline
from middlewares.user_agent_middleware import RotatingUserAgentMiddleware
from utils.sheet_writer import write_properties
import sys
import os

# -- Windows Unicode Fix --
if os.name == "nt":
    try:
        import ctypes
        ctypes.windll.kernel32.SetConsoleOutputCP(65001)
    except Exception:
        pass

# -- Logging Configuration --
logger = logging.getLogger()
logger.setLevel(logging.INFO)
if logger.hasHandlers():
    logger.handlers.clear()

file_handler = logging.FileHandler("scraper.log", mode='a', encoding='utf-8')
file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger.addHandler(file_handler)

console_handler = logging.StreamHandler(stream=sys.stdout)
console_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger.addHandler(console_handler)

# -- Helper Functions --
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

def extract_property_details(li_elements):
    # REDACTED: Custom parsing logic for beds/baths/toilets
    return "N/A", "N/A", "N/A"

def parse_price_to_int(price_str):
    if not price_str or price_str == "N/A":
        return None
    cleaned = re.sub(r'[^\d]', '', price_str)
    return int(cleaned) if cleaned.isdigit() else None

# -- URL Templates --
categories = {
    "house": "https://example.com/category/house/in/{}",
    "land": "https://example.com/category/land/in/{}",
    "flat-apartment": "https://example.com/category/flat-apartment/in/{}",
    "commercial-property": "https://example.com/category/commercial-property/in/{}"
}

def build_url(category, state, city):
    # REDACTED: Generates target URL
    return f"https://example.com/{category}/{state}/{city}"

# -- Scraper Core --
def scrape_category_city(playwright, context, category, city, state, pipeline):
    page = context.new_page()
    listings_data = []
    url = build_url(category, state, city)
    logging.info(f"Scraping {category} in {city}, {state} from {url}")

    try:
        page.goto(url, timeout=60000)
        time.sleep(3)
    except Exception as e:
        logging.error(f"❌ Failed to load {url}: {e}")
        context.close()
        return []

    max_pages = 1
    page_count = 0

    while True:
        page_count += 1
        if page_count > max_pages:
            logging.info("🛑 Max page limit reached.")
            break

        try:
            listings = page.query_selector_all('div.listing')
        except Exception as e:
            logging.error(f"❌ Failed to find listings: {e}")
            break

        listing_page = context.new_page()

        for listing in listings:
            try:
                full_url = "https://example.com/dummy-url"

                # REDACTED: Data extraction (title, price, agent, location, phone)
                listing_data = {
                    "website": "example.com",
                    "category": category,
                    "city": city,
                    "title": "REDACTED",
                    "price": "REDACTED",
                    "price_int": 0,
                    "location": "REDACTED",
                    "bedrooms": "N/A",
                    "bathrooms": "N/A",
                    "toilets": "N/A",
                    "agent_name": "REDACTED",
                    "agent_call": "REDACTED",
                    "image_url": "https://example.com/image.jpg",
                    "url": full_url,
                    "date_scraped": datetime.utcnow()
                }

                pipeline.process_item(listing_data)
                listings_data.append(listing_data)
                logging.info(pformat(listing_data, sort_dicts=False))

            except Exception as e:
                logging.error(f"❌ Listing scrape error: {e}")

        listing_page.close()
        break  # REDACTED: Pagination logic ends here

    return listings_data

# -- Main Runner --
def main():
    pipeline = MongoPipeline()
    pipeline.open()

    listings_all = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        context.set_default_timeout(60000)

        cities_by_state = {
            "state-1": ["city-a"],
            "state-2": ["city-b"]
        }

        middleware = RotatingUserAgentMiddleware()
        context.route("**/*", middleware)

        for category in categories:
            for state, cities_list in cities_by_state.items():
                for city in cities_list:
                    listings = scrape_category_city(p, context, category, city, state, pipeline)
                    listings_all.extend(listings)

        context.close()
        browser.close()

    pipeline.close()
    write_properties(listings_all, website="example.com", clear_first=True, prepend=True)
    logging.info("✅ Scraping complete.")

if __name__ == "__main__":
    main()
