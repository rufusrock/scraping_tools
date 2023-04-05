import sqlite3
import csv

conn = sqlite3.connect('amazon_search_scrape.db')
c = conn.cursor()

# Create the 'products' table
c.execute('''CREATE TABLE products (
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
c.execute('''CREATE TABLE search_terms (
                id INTEGER PRIMARY KEY,
                search_term TEXT NOT NULL UNIQUE,
                main_category TEXT NOT NULL UNIQUE
            )''')

# Create the 'locations' table
c.execute('''CREATE TABLE locations (
                id INTEGER PRIMARY KEY,
                location TEXT NOT NULL UNIQUE,
                ip_address TEXT NOT NULL UNIQUE,
                MULLVAD_NODE TEXT NOT NULL UNIQUE
            )''')

# Create the 'search_results' table
c.execute('''CREATE TABLE search_results (
                id INTEGER PRIMARY KEY,
                time TEXT NOT NULL,
                search_term_id INTEGER,
                location_id INTEGER,
                position_within_listing_type INTEGER,
                ad BOOLEAN,
                listing_type TEXT,
                average_rating REAL,
                no_of_ratings INTEGER,
                save_coupon BOOLEAN,
                bundles_available BOOLEAN,
                limited_time_deal BOOLEAN,
                amazons_choice BOOLEAN,
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
                FOREIGN KEY (search_term_id) REFERENCES search_terms (id),
                FOREIGN KEY (location_id) REFERENCES locations (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            )''')

#insert our list of search terms and main_categories from the csv
def insert_search_terms_from_csv():
    filename = "queries.csv"
    with open(filename, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            search_term = row["query"]
            main_category = row["category"]
            insert_search_term(search_term, main_category)

def insert_search_term(search_term, main_category):
    with sqlite3.connect('amazon_search_scrape.db') as conn:
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO search_terms (search_term, main_category) VALUES (?,?)", (search_term, main_category))
        conn.commit()
        c.execute("SELECT id FROM search_terms WHERE search_term = ?", (search_term,))
        return c.fetchone()[0]

def print_search_terms():
    with sqlite3.connect('amazon_search_scrape.db') as conn:
        c = conn.cursor()
        c.execute("SELECT id, search_term FROM search_terms")
        search_terms = c.fetchall()
        print("[+] Search Terms: ")
        for term_id, term in search_terms:
            print(f"{term_id}: {term}")

insert_search_terms_from_csv()
print_search_terms()
# Commit the changes and close the connection
conn.commit()
conn.close()