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
                search_term TEXT PRIMARY KEY,
                main_category TEXT NOT NULL,
                location TEXT NOT NULL,
                mullvad_node TEXT NOT NULL,
                date_completed TEXT
            )''')
# Create the 'product_scrape_details' table
c.execute('''CREATE TABLE product_scrape_details (
                id INTEGER PRIMARY KEY,
                time TEXT NOT NULL,
                date TEXT NOT NULL,
                product_id INTEGER,
                location TEXT,
                search_term_id INTEGER
            )''')


# Create the 'search_results' table
c.execute('''CREATE TABLE search_results (
                id INTEGER PRIMARY KEY,
                time TEXT NOT NULL,
                search_term_id INTEGER,
                position_within_listing_type INTEGER,
                ad BOOLEAN,
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
                FOREIGN KEY (search_term_id) REFERENCES search_terms (id),
                FOREIGN KEY (location_id) REFERENCES product_scrape_details (id),
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
    with sqlite3.connect('ecommerce.db') as conn:
        c = conn.cursor()
        try:
            c.execute("INSERT INTO search_terms (search_term, main_category) VALUES (?, ?)",
                      (search_term, main_category))
            conn.commit()
        except sqlite3.IntegrityError:
            pass  # Search term already exists, do nothing


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