import sqlite3
import csv

conn = sqlite3.connect('amazon_search_scrape.db')
c = conn.cursor()

# Create the 'products' table
c.execute('''CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                product_name TEXT NOT NULL,
                url TEXT NOT NULL,
                current_price REAL,
                list_price REAL,
                discount_percentage REAL,
                amazons_choice_product_page BOOLEAN,
                best_seller_product_page BOOLEAN,
                prime_product_page BOOLEAN,
                fakespot_rating REAL,
                unit_price REAL,
                alternate_product_options_available BOOLEAN,
                no_possible_product_configurations INTEGER,
                amazon_brand TEXT,
                shipping_price REAL,
                shipping_time TEXT,
                available_new BOOLEAN,
                available_used BOOLEAN,
                sold_by TEXT,
                dispatches_from TEXT,
                returns_policy TEXT,
                date_of_first_review TEXT,
                five_star_review_percentage REAL,
                four_star_review_percentage REAL,
                three_star_review_percentage REAL,
                two_star_review_percentage REAL,
                one_star_review_percentage REAL,
                product_category_one TEXT,
                product_category_two TEXT,
                product_category_three TEXT,
                product_category_four TEXT,
                product_category_five TEXT,
                review_one_text TEXT,
                review_one_rating REAL,
                review_two_text TEXT,
                review_two_rating REAL,
                review_three_text TEXT,
                review_three_rating REAL,
                review_four_text TEXT,
                review_four_rating REAL,
                review_five_text TEXT,
                review_five_rating REAL
            )''')

# Create the 'search_terms' table
c.execute('''CREATE TABLE IF NOT EXISTS search_terms (
                search_term TEXT PRIMARY KEY,
                main_category TEXT NOT NULL,
                location TEXT,
                mullvad_node TEXT,
                date_completed TEXT,
                time_to_complete TEXT
            )''')

# Create the 'search_results' table
c.execute('''CREATE TABLE IF NOT EXISTS search_results (
                id INTEGER PRIMARY KEY,
                time TEXT NOT NULL,
                name TEXT,
                search_term TEXT NOT NULL,
                position_within_listing_type INTEGER,
                ad BOOLEAN,
                price REAL,
                listing_type TEXT,
                average_rating REAL,
                no_of_ratings INTEGER,
                save_coupon BOOLEAN,
                bundles_available BOOLEAN,
                limited_time_deal BOOLEAN,
                amazons_choice BOOLEAN,
                amazon_brand BOOLEAN,
                best_seller BOOLEAN,
                prime BOOLEAN,
                url TEXT,
                small_business BOOLEAN,
                search_result_size INTEGER,
                search_result_window_percentage REAL,
                search_result_html_body_percentage REAL,
                search_result_y_coord REAL,
                search_result_x_coord REAL,
                no_of_scrolls_for_visibility INTEGER,
                FOREIGN KEY (search_term) REFERENCES search_terms (search_term)
            )''')

conn.commit()

def insert_search_terms_from_csv():
    filename = "queries.csv"
    with sqlite3.connect('amazon_search_scrape.db') as conn:
        with open(filename, 'r') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                search_term = row.get('query')
                main_category = row.get('category')
                if search_term and main_category:
                    conn.execute("INSERT INTO search_terms (search_term, main_category) VALUES (?, ?)",
                                 (search_term, main_category))
        conn.commit()

def print_search_terms():
    with sqlite3.connect('amazon_search_scrape.db') as conn:
        c = conn.cursor()
        c.execute("SELECT search_term, main_category FROM search_terms")
        search_terms = c.fetchall()
        print("[+] Search Terms: ")
        for term, main_category in search_terms:
            print(f"{term}: {main_category}")

insert_search_terms_from_csv()
print_search_terms()

# Commit the changes and close the connection
conn.commit()
conn.close()