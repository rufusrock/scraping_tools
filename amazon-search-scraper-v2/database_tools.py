import datetime
import sqlite3

# Define search_result table column names as constants
TIME = "time"
NAME = "name"
SEARCH_TERM = "search_term"
POSITION_WITHIN_LISTING_TYPE = "position_within_listing_type"
AD = "ad"
PRICE = "price"
LISTING_TYPE = "listing_type"
AVERAGE_RATING = "average_rating"
NO_OF_RATINGS = "no_of_ratings"
SAVE_COUPON = "save_coupon"
BUNDLES_AVAILABLE = "bundles_available"
LIMITED_TIME_DEAL = "limited_time_deal"
AMAZONS_CHOICE = "amazons_choice"
AMAZON_BRAND = "amazon_brand"
BEST_SELLER = "best_seller"
PRIME = "prime"
URL = "url"
SMALL_BUSINESS = "small_business"
SEARCH_RESULT_SIZE = "search_result_size"
SEARCH_RESULT_WINDOW_PERCENTAGE = "search_result_window_percentage"
SEARCH_RESULT_HTML_BODY_PERCENTAGE = "search_result_html_body_percentage"
SEARCH_RESULT_Y_COORD = "search_result_y_coord"
SEARCH_RESULT_X_COORD = "search_result_x_coord"
NO_OF_SCROLLS_FOR_VISIBILITY = "no_of_scrolls_for_visibility"

def insert_search_result(search_result):
    # Sanitize input data
    for key in search_result:
        if type(search_result[key]) == str:
            search_result[key] = search_result[key].strip()

    try:
        with sqlite3.connect("amazon_search_scrape.db") as conn:
            c = conn.cursor()
            c.execute(
                f"INSERT INTO search_results ({TIME}, {NAME}, {PRICE}, {SEARCH_TERM}, {POSITION_WITHIN_LISTING_TYPE}, {AD}, {LISTING_TYPE}, "
                f"{AVERAGE_RATING}, {NO_OF_RATINGS}, {SAVE_COUPON}, {BUNDLES_AVAILABLE}, {LIMITED_TIME_DEAL}, {AMAZONS_CHOICE}, "
                f"{BEST_SELLER}, {PRIME}, {URL}, {SMALL_BUSINESS}, {SEARCH_RESULT_SIZE}, {SEARCH_RESULT_WINDOW_PERCENTAGE}, "
                f"{SEARCH_RESULT_HTML_BODY_PERCENTAGE}, {SEARCH_RESULT_Y_COORD}, {SEARCH_RESULT_X_COORD}, "
                f"{NO_OF_SCROLLS_FOR_VISIBILITY}, {AMAZON_BRAND}) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    search_result[TIME], search_result[NAME], search_result[PRICE], search_result[SEARCH_TERM], search_result[POSITION_WITHIN_LISTING_TYPE],
                    search_result[AD], search_result[LISTING_TYPE], search_result[AVERAGE_RATING], search_result[NO_OF_RATINGS],
                    search_result[SAVE_COUPON], search_result[BUNDLES_AVAILABLE], search_result[LIMITED_TIME_DEAL],
                    search_result[AMAZONS_CHOICE], search_result[BEST_SELLER], search_result[PRIME], search_result[URL],
                    search_result[SMALL_BUSINESS], search_result[SEARCH_RESULT_SIZE], search_result[SEARCH_RESULT_WINDOW_PERCENTAGE],
                    search_result[SEARCH_RESULT_HTML_BODY_PERCENTAGE], search_result[SEARCH_RESULT_Y_COORD],
                    search_result[SEARCH_RESULT_X_COORD], search_result[NO_OF_SCROLLS_FOR_VISIBILITY], search_result[AMAZON_BRAND]
                )
            )
            conn.commit()
            return c.lastrowid
    except sqlite3.Error as e:
        print(f"Error inserting search result: {e}")
        return None
    
def get_unscraped_search_terms():
    with sqlite3.connect('amazon_search_scrape.db') as conn:
        c = conn.cursor()
        c.execute('''SELECT search_term FROM search_terms WHERE date_completed IS NULL''')
        return c.fetchall()
    
def update_search_term(search_term, location, mullvad_node, time_taken):
    date_completed = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with sqlite3.connect('amazon_search_scrape.db') as conn:
        c = conn.cursor()
        c.execute('''UPDATE search_terms
                     SET date_completed = ?, location = ?, mullvad_node = ?, time_to_complete = ?
                     WHERE search_term = ?''', (date_completed, location, mullvad_node, time_taken, search_term))
        conn.commit()

#all the product stuff below 