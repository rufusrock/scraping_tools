from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import NoSuchElementException
from random import choice
import time
import urllib.request
from twocaptcha import TwoCaptcha
from tqdm import tqdm
import os
import subprocess
import re
from database_tools import *

FILEPATH = "C://Users//Rufus//scripts//scraping_tools//amazon-search-scraper-v2"
BINARY_LOCATION = r"C://Program Files//Mozilla Firefox//firefox.exe"
FILEPATH_TO_2CATPCHA_API_KEY = r"C://Users//Rufus//OneDrive//Desktop//credentials.txt"

#get the api key from the text file in home directory
with open(FILEPATH_TO_2CATPCHA_API_KEY, "r", encoding="UTF-8") as f:
    API_KEY = f.readline()
    f.close()

TWOCAPTCHA_API_KEY = os.getenv("APIKEY_2CAPTCHA", API_KEY)

#looks for captcha and solves it
def captcha_solver(browser):
    try:
        captcha = WebDriverWait(browser, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "form[action='/errors/validateCaptcha']")))
        if captcha:
            solver = TwoCaptcha(TWOCAPTCHA_API_KEY)
            try:
                print("[+] Solving Captcha")
                image_url = captcha[0].find_element(By.TAG_NAME, "img").get_attribute("src")
                # Download the captcha image and save it to a file
                urllib.request.urlretrieve(image_url, "captcha.jpg")
                result = solver.normal("captcha.jpg")
                print(result)
                os.remove("captcha.jpg")
                text_form = browser.find_element(By.CSS_SELECTOR, "input[id='captchacharacters']")
                text_form.clear()
                send_string = result["code"].upper()
                text_form.send_keys(send_string)
                text_form.send_keys(Keys.RETURN)
            except NoSuchElementException:
                print("[+] Captcha element not found")
            except Exception as e:
                print(f"[-] Unexpected error: {e}")
    except:
        print("[+] No Captcha Found")
        pass

#gets all the relevant size information about the product from the webpage
def get_size_stats(browser, element, product_data):
    if element.is_displayed() == True:
        element_size = [element.size["width"], element.size["height"]]
        element_area = element.size["width"] * element.size["height"]
        screen_area = browser.get_window_size()["width"] * browser.get_window_size()["height"]
        element_y_coord = element.location["y"]
        no_of_scrolls = element_y_coord /  browser.get_window_size()["height"]
        element_x_coord = element.location["x"]
        body_area = browser.find_element(By.TAG_NAME, "body").size["width"] * browser.find_element(By.TAG_NAME, "body").size["height"]
        body_percentage = (element_area / body_area) * 100

        product_data["search_result_size"] = element_area
        product_data["search_result_window_percentage"] = (element_area / screen_area) * 100
        product_data["search_result_y_coord"] = element_y_coord
        product_data["search_result_x_coord"] = element_x_coord
        product_data["no_of_scrolls_for_visibility"] = no_of_scrolls
        product_data["search_result_html_body_percentage"] = body_percentage
    else:
        product_data["search_result_size"] = "Not Visible"
        product_data["search_result_window_percentage"] = "Not Visible"
        product_data["search_result_y_coord"] = "Not Visible"
        product_data["search_result_x_coord"] = "Not Visible"
        product_data["no_of_scrolls_for_visibility"] =  "Not Visible"
        product_data["search_result_html_body_percentage"] = "Not Visible"

    return product_data 

def find_element(search_result, locator):
    try:
        return search_result.find_element(*locator)
    except NoSuchElementException:
        return None
    
def get_search_result_data(browser, search_result, product_data):
    #Checks if the product is an ad
    sponsored_span_text = find_element(search_result, (By.CSS_SELECTOR, "span[class='puis-label-popover-default']"))
    if sponsored_span_text:
        product_data["ad"] = True
    else:
        product_data["ad"] = False

    #get the product name
    try:
        name = search_result.find_element(By.CSS_SELECTOR, "span[class='a-size-medium a-color-base a-text-normal']")
        product_data["name"] = name.get_attribute("innerHTML")
    except NoSuchElementException:
        name = find_element(search_result, (By.CSS_SELECTOR, "span.a-size-base-plus.a-color-base.a-text-normal"))
        if name:
            product_data["name"] = name.get_attribute("innerHTML")

    # Get the product price
    current_price = find_element(search_result, (By.CSS_SELECTOR, "span.a-offscreen"))
    if current_price:
        product_data["price"] = current_price.get_attribute("innerHTML")
    else:
        product_data["price"] = "ERROR - Out of Stock?"

    # Get the product rating
    rating_list = find_element(search_result, (By.CSS_SELECTOR, "span[class='a-icon-alt']"))
    if rating_list:
        rating_list = rating_list.get_attribute("innerHTML").split(" ")
        for string in rating_list:
            if "." in string:
                product_data["average_rating"] = string
                break
    else:
        product_data["average_rating"] = "No Rating"

    # Check if Amazon brand logo is present in the listing
    amazon_banner = find_element(search_result, (By.CSS_SELECTOR, "span[class='a-color-state.puis-light-weight-text']"))
    if amazon_banner:
        product_data["amazon_brand"] = True
    else:
        product_data["amazon_brand"] = False

    # Check if Prime logo is present in the listing
    prime_logo = find_element(search_result, (By.CSS_SELECTOR, "i.a-icon.a-icon-prime.a-icon-medium"))
    if prime_logo:
        product_data["prime"] = True
    else:
        product_data["prime"] = False
    
    # Look for Best Seller and Amazon's Choice icons in product listing
    icon_element = find_element(search_result, (By.CSS_SELECTOR, "span.a-badge-label-inner.a-text-ellipsis"))
    if icon_element:
        if "Best" in icon_element.find_element(By.CSS_SELECTOR, "span").text:
            product_data["best_seller"] = True
            product_data["amazons_choice"] = False
        elif "Amazon" in icon_element.find_element(By.CSS_SELECTOR, "span").text:
            product_data["amazons_choice"] = True
            product_data["best_seller"] = False
        else:
            product_data["best_seller"] = False
            product_data["amazons_choice"] = False
    else:
        product_data["best_seller"] = False
        product_data["amazons_choice"] = False

    #look for a limited time deal icon in the product listing and set limited time deal status to true if it is found
    limited_time_deal = find_element(search_result, (By.CSS_SELECTOR, "span[data-a-badge-color='sx-lightning-deal-red']"))

    if limited_time_deal:
            if limited_time_deal.find_element(By.CSS_SELECTOR, "span[class='a-badge-text']").text != "":
                product_data["limited_time_deal"] = True
    else:
        product_data["limited_time_deal"] = False

    # Look for Save coupon icon in the product listing
    save_coupon = find_element(search_result, (By.CSS_SELECTOR, "span[class='a-size-base s-highlighted-text-padding aok-inline-block s-coupon-highlight-color']"))
    if save_coupon and "Save" in save_coupon.text:
        save_string = save_coupon.text.split(" ")
        for part in save_string:
            if "$" in part or "%" in part:
                product_data["save_coupon"] = part
                break
    else:
        product_data["save_coupon"] = "None"
    
    # Check if Small Business icon is present in the product listing
    labels = search_result.find_elements(By.CSS_SELECTOR, "img[class='s-image']")
    if labels:
        product_data["small_business"] = False
        for label in labels:
            if label.get_attribute("src") == "https://m.media-amazon.com/images/I/111mHoVK0kL._SS200_.png":
                product_data["small_business"] = True
                break
    else:
        product_data["small_business"] = False
    

    # Check if Bundles are available in the product listing
    links = search_result.find_elements(By.CSS_SELECTOR, "a[class='a-link-normal s-underline-text s-underline-link-text s-link-style']")
    if links:
        product_data["bundles_available"] = False
        for link in links:
            if "Bundles" in link.text:
                product_data["bundles_available"] = True
                break
    else:
        product_data["bundles_available"] = False

    # Get the product URL
    href = find_element(search_result, (By.CSS_SELECTOR, "a[class='a-link-normal s-no-outline']"))
    if href:
        href = href.get_attribute("href")
        if "amazon.com" in href:
            product_data["url"] = href
        else:
            product_data["url"] = "https://www.amazon.com" + href
    else:
        product_data["url"] = "ERROR"

     # Get the product's number of reviews
    no_of_reviews = find_element(search_result, (By.CSS_SELECTOR, "span.a-size-base.s-underline-text"))
    if no_of_reviews:
        product_data["no_of_ratings"] = no_of_reviews.text.replace(",", "")
    else:
        product_data["no_of_ratings"] = "None"

    product_data = get_size_stats(browser, search_result, product_data)

    return product_data
    
def create_search_result_dict(search_term):
    search_result = {
        "time": time.time(),
        "name": None,
        "position_within_listing_type": None, 
        "ad": None,
        "price": None,
        "search_term": search_term,
        "listing_type": None,
        "average_rating": None,
        "no_of_ratings": None,
        "save_coupon": None,
        "bundles_available": None,
        "limited_time_deal": None,
        "amazons_choice": None,
        "best_seller": None,
        "prime": None,
        "url": None,
        "amazon_brand": None,
        "small_business": None,
        "search_result_size": None,
        "search_result_window_percentage": None,
        "search_result_html_body_percentage": None,
        "search_result_y_coord": None,
        "search_result_x_coord": None,
        "no_of_scrolls_for_visibility": None,
    }
    return search_result

def main():
    options = Options()
    #set the browser to headless mode [UNCOMMENT TO RUN WITHOUT BROWSER GUI] (Minor performance boost)
    #options.add_argument("-headless")

    #anti detection measures
    options.set_preference("dom.webdriver.enabled", False)
    options.set_preference("useAutomationExtension", False)
    options.binary_location = BINARY_LOCATION #locates the firefox binary

    # Initializing a list with two Useragents 
    useragentlist = [ 
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.164 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.190 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36",
    ] 

    user_agent = choice(useragentlist)

    options.set_preference("dom.webdriver.enabled", False)
    options.set_preference("useAutomationExtension", False)
    options.set_preference("dom.webnotifications.enabled", False)
    options.set_preference("dom.push.enabled", False)
    options.set_preference("general.useragent.override", user_agent)

    browser = webdriver.Firefox(options=options) #opens the browser

    browser.get("https://www.amazon.com") #consider the effect of going through google? might be worth adding a feature to test for impact? 

    print(f"[+] Connected to Mullvad node {mullvad_node} in {location}")
    time.sleep(2)

    captcha_solver(browser)
    #sometimes you get a double captcha here so we need to solve it again (if there isn't one only adds 10 seconds once not a huge deal)
    captcha_solver(browser)

    browser.refresh() #refreshes the page because sometimes amazon loads with wierd formatting and this fixes it

    unscraped_search_terms = get_unscraped_search_terms()

    for (search_term,) in tqdm(unscraped_search_terms, desc="Search Terms", unit="search term"):
        search_term_run_time = time.time()
        network_info = subprocess.run(["mullvad", "status"], capture_output=True, text=True).stdout

        location = network_info.split("in")[-1].strip() #much faster location detection than using geoip
        mullvad_node = network_info.split(" ")[2].strip() #could be relevant - might be able to see in data if there is a correlation between node and ad prevelance

        print(f"[+] Scraping search term {search_term}")

        search_bar = WebDriverWait(browser, 20).until(EC.presence_of_element_located((By.ID, "twotabsearchtextbox")))
        search_bar.clear()
        search_bar.send_keys(search_term)
        search_bar.send_keys(Keys.RETURN)
        
        search_results, carousels, video_elements, banner_elements = None, None, None, None #resetting these variables because I was getting weird DOM expired errors

        time.sleep(5) #wait for page to load
        
        search_results = WebDriverWait(browser, 20).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[data-component-type='s-search-result']")))
        carousels = browser.find_elements(By.CSS_SELECTOR, "span[data-component-type='s-searchgrid-carousel']")
        video_elements = browser.find_elements(By.CSS_SELECTOR, "div[class='a-section sbv-video aok-relative sbv-vertical-center-within-parent']")
        banner_elements = browser.find_elements(By.CSS_SELECTOR, "div[class='s-result-item s-widget s-widget-spacing-large AdHolder s-flex-full-width']")
        
        result_position = 1

        for result in tqdm(search_results, desc="Search Results", unit="result", leave=False):
            listing_type = "Results"
            search_result = create_search_result_dict(search_term)
            search_result["listing_type"] = listing_type
            search_result["position_within_listing_type"] = result_position
            search_result = get_search_result_data(browser, result, search_result)

            insert_search_result(search_result)
            result_position += 1
        
        carousel_counter = 1
        for carousel in tqdm(carousels, desc="Carousels", unit="carousel", leave=False):
            if carousel.is_displayed():
                listing_type = carousel.find_element(By.XPATH, ".//preceding::span[contains(@class,'a-size-medium-plus') and contains(@class,'a-color-base')][1]")
                listing_type = listing_type.get_attribute("innerHTML")

                carousel_products = carousel.find_elements(By.CSS_SELECTOR, "li[class^='a-carousel-card']")
                product_position = 1
                for product in carousel_products:

                    search_result = create_search_result_dict(search_term)
                    
                    ad_section_heading_keywords = ["rated", "frequently", "choice", "recommendations", "top", "our", "recommendations", "editorial", "best"]
                    if any(x in listing_type.lower() for x in ad_section_heading_keywords):
                        search_result["ad"] = True
                    search_result["listing_type"] = "Carousel_" + re.sub(r'\s+', '', listing_type)
                    

                    search_result["position_within_listing_type"] = product_position
                    search_result = get_search_result_data(browser, product, search_result)
                    product_position += 1
                    insert_search_result(search_result)

            carousel_counter += 1

        video_position = 1
        for video_element in tqdm(video_elements, desc="Videos", unit="video", leave=False):
            if video_element.is_displayed():
                search_result = create_search_result_dict(search_term)

                search_result["url"] = video_element.find_element(By.CSS_SELECTOR, "a[class^='a-link-normal']").get_attribute("href")
                search_result["ad"] = True
                search_result["listing_type"] = "Video" 
                search_result["position_within_listing_type"] = video_position
                search_result["amazons_choice"] = "NA"
                search_result["best_seller"] = "NA"
                search_result["prime"] = "NA"
                search_result["average_rating"] = "NA"
                search_result["no_of_ratings"] = "NA"
                search_result["name"] = "NA"
                search_result["amazon_brand"] = "NA"
                search_result["price"] = "NA"
                search_result["save_coupon"] = "NA"
                search_result["limited_time_deal"] = "NA"
                search_result["bundles_available"] = "NA"
                search_result["small_business"] = "NA"

                parent = video_element.find_element(By.XPATH, '..')
                while True:
                    if "sg-row" in parent.get_attribute("class"):
                        break
                    parent = parent.find_element(By.XPATH, '..')
    
                search_result = get_size_stats(browser, video_element, search_result)

                insert_search_result(search_result)

                video_position += 1

        banner_position = 1
        for banner_element in tqdm(banner_elements, desc="Banners", unit="banner", leave=False):
            if banner_element.is_displayed():
                search_result = create_search_result_dict(search_term)

                search_result["url"] = banner_element.find_element(By.CSS_SELECTOR, "a[class^='a-link-normal']").get_attribute("href")
                search_result["ad"] = True
                search_result["listing_type"] = "Banner"
                search_result["amazons_choice"] = "NA"
                search_result["best_seller"] = "NA"
                search_result["prime"] = "NA"
                search_result["price"] = "NA"
                search_result["name"] = "NA"
                search_result["amazon_brand"] = "NA"
                search_result["average_rating"] = "NA"
                search_result["no_of_ratings"] = "NA"
                search_result["save_coupon"] = "NA"
                search_result["limited_time_deal"] = "NA"
                search_result["bundles_available"] = "NA"
                search_result["small_business"] = "NA"
                search_result["position_within_listing_type"] = banner_position
                search_result = get_size_stats(browser, banner_element, search_result)

                insert_search_result(search_result)
                banner_position += 1

        search_term_run_time = time.time() - search_term_run_time
        update_search_term(search_term, location, mullvad_node, search_term_run_time)
        print("[+] Done " + search_term + " " + str(round(search_term_run_time/60, 2)) + " minutes")

    browser.quit()

if __name__ == "__main__":
    main()