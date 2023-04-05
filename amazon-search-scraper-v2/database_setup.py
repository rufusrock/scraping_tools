import sqlite3

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
                ip_address TEXT NOT NULL UNIQUE
            )''')

# Create the 'search_results' table
c.execute('''CREATE TABLE search_results (
                id INTEGER PRIMARY KEY,
                time TEXT NOT NULL,
                search_term_id INTEGER,
                location_id INTEGER,
                product_id INTEGER,
                ad BOOLEAN,
                listing_type TEXT,
                average_rating REAL,
                no_of_reviews INTEGER,
                position_within_section INTEGER,
                save_coupon_search_label_present BOOLEAN,
                bundles_available BOOLEAN,
                limited_time_deal_search_label_present BOOLEAN,
                amazons_choice_search_label_present BOOLEAN,
                best_seller_search_label_present BOOLEAN,
                prime_search_label_present BOOLEAN,
                small_business BOOLEAN,
                search_result_size INTEGER,
                search_result_window_percentage REAL,
                search_result_html_body_percentage REAL,
                search_result_y_coord REAL,
                search_result_x_coord REAL,
                no_of_scrolls_for_product_visibility INTEGER,
                FOREIGN KEY (search_term_id) REFERENCES search_terms (id),
                FOREIGN KEY (location_id) REFERENCES locations (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            )''')

# Commit the changes and close the connection
conn.commit()
conn.close()