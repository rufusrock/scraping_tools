import datetime
import sqlite3

def update_search_term(search_term_id, location):
    date_completed = datetime.datetime.now().strftime("%Y-%m-%d")
    with sqlite3.connect('ecommerce.db') as conn:
        c = conn.cursor()
        c.execute('''UPDATE search_terms
                     SET location = ?, date_completed = ?
                     WHERE id = ?''', (location, date_completed, search_term_id))
        conn.commit()

def insert_search_result(search_result):

    with sqlite3.connect('ecommerce.db') as conn:
        c = conn.cursor()
        c.execute('''INSERT INTO search_results (
                        time, search_term_id, location_id, position_within_section, ad, listing_type,
                        average_rating, no_of_reviews, save_coupon_search_label_present, bundles_available,
                        limited_time_deal_search_label_present, amazons_choice_search_label_present, best_seller_search_label_present,
                        prime_search_label_present, url, small_business, search_result_size,
                        search_result_window_percentage, search_result_html_body_percentage, search_result_y_coord,
                        search_result_x_coord, no_of_scrolls_for_product_visibility
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (
                        search_result["time"], search_result["search_term_id"],
                        search_result["position_within_listing_type"], search_result["ad"], search_result["listing_type"],
                        search_result["average_rating"], search_result["no_of_ratings"], search_result["save_coupon"],
                        search_result["bundles_available"], search_result["limited_time_deal"], search_result["amazon_choice"],
                        search_result["best_seller"], search_result["prime"], search_result["url"],
                        search_result["small_business"], search_result["search_result_size"],
                        search_result["search_result_window_percentage"], search_result["search_result_html_body_percentage"],
                        search_result["search_result_y_coord"], search_result["search_result_x_coord"],
                        search_result["no_of_scrolls_for_visibility"]
                    ))
        conn.commit()
        return c.lastrowid
    
def get_unscraped_search_terms():
    with sqlite3.connect("amazon_search_scrape.db") as conn:
        c = conn.cursor()
        c.execute('''SELECT id, search_term FROM search_terms WHERE NOT EXISTS (
            SELECT 1 FROM search_results WHERE product_data.search_term_id = search_terms.id
        )''')
        return c.fetchall()