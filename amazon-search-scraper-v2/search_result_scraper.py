from selenium import webdriver
#from seleniumwire import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import NoSuchElementException
import requests
from random import randint, choice
import time
import shutil
import urllib.request
from datetime import datetime
from twocaptcha import TwoCaptcha
import csv
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
    captcha = WebDriverWait(browser, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "form[action='/errors/validateCaptcha']")))
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
            text_form.send_keys(result["code"].capitalize())
            text_form.send_keys(Keys.RETURN)
        except NoSuchElementException:
            print("[+] Captcha element not found")
        except Exception as e:
            print(f"[-] Unexpected error: {e}")

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
        product_data["no_of_scrolls_for_product_visibility"] = no_of_scrolls
        product_data["search_result_html_body_percentage"] = body_percentage
    else:
        product_data["search_result_size"] = "Not Visible"
        product_data["search_result_window_percentage"] = "Not Visible"
        product_data["search_result_y_coord"] = "Not Visible"
        product_data["search_result_x_coord"] = "Not Visible"
        product_data["no_of_scrolls_for_product_visibility"] =  "Not Visible"
        product_data["search_result_html_body_percentage"] = "Not Visible"

    return product_data 

def get_search_result_data(browser, search_result, product_data):
    #Checks if the product is an ad

    try:
        sponsored_span_text = search_result.find_elements(By.CSS_SELECTOR, "span.puis-label-popover-default")
    except NoSuchElementException:
        product_data["ad"] = False

    if sponsored_span_text:
        if "Sponsored" in sponsored_span_text[0].find_element(By.CSS_SELECTOR, "span").text or "AdHolder" in search_result.get_attribute("class"):
            if "Carousel" not in product_data["listing_type"]:
                product_data["listing_type"] = "Search Injected Ad"
                product_data["ad"] = True

    #get the product name
    try:
        name = search_result.find_element(By.CSS_SELECTOR, "span.a-size-medium.a-color-base.a-text-normal")
        product_data["product_name"] = name.text
    except NoSuchElementException:
        name = search_result.find_element(By.CSS_SELECTOR, "span.a-size-base-plus.a-color-base.a-text-normal")
        if name:
            product_data["product_name"] = name.text

    #get the product price
    try:
        current_price = search_result.find_element(By.CSS_SELECTOR, "span.a-offscreen")
    except NoSuchElementException:
        product_data["current_price"] = "ERROR - Out of Stock?"

    if current_price:
        product_data["current_price"] = current_price.text

    #get the product rating
    try:
        rating_list = search_result.find_element(By.CSS_SELECTOR, "span.a-icon-alt")
    except NoSuchElementException:
        product_data["average_rating"] = "No Rating"
    
    if rating_list:
            rating_list = rating_list.text.split(" ")
            for string in rating_list:
                if "." in string:
                    product_data["average_rating"] = string
                    break

    #if there is an amazon brand logo in the listing set the amazon brand status to true 
    try:
        amazon_banner = search_result.find_element(By.CSS_SELECTOR, "span.a-color-state.puis-light-weight-text")
    except NoSuchElementException:
        product_data["amazon_brand"] = False

    if amazon_banner:
            product_data["amazon_brand"] = True

    #if there is a prime logo in the listing set the prime search status to true
    try:
        prime_logo = search_result.find_element(By.CSS_SELECTOR, "i.a-icon.a-icon-prime.a-icon-medium")
    except NoSuchElementException:
        product_data["prime"] = False
    
    if prime_logo:
            product_data["prime"] = True
    
    #look for best seller icon in product listing and set best seller status to true if it is found
    try:   
        icon_element = search_result.find_element(By.CSS_SELECTOR, "span.a-badge-label-inner.a-text-ellipsis")
    except NoSuchElementException:
        product_data["best_seller"] = False
        product_data["amazons_choice"] = False

    if icon_element:
            if "Best" in icon_element.find_element(By.CSS_SELECTOR, "span").text:
                product_data["best_seller"] = True
            elif "Amazon" in icon_element.find_element(By.CSS_SELECTOR, "span").text:
                product_data["amazons_choice"] = True

    #look for a limited time deal icon in the product listing and set limited time deal status to true if it is found
    try:
        limited_time_deal = search_result.find_element(By.CSS_SELECTOR, "span[data-a-badge-color='sx-lightning-deal-red']")
    except NoSuchElementException:
        product_data["limited_time_deal"] = False

    if limited_time_deal:
            if limited_time_deal.find_element(By.CSS_SELECTOR, "span.a-badge-text").text:
                product_data["limited_time_deal"] = True
        
    #look for a save coupon icon in the product listing and set save coupon status to true if it is found
    try:
        save_coupon = search_result.find_element(By.CSS_SELECTOR, "span[class='a-size-base s-highlighted-text-padding aok-inline-block s-coupon-highlight-color']")
    except NoSuchElementException:
        product_data["save_coupon"] = False

    if save_coupon:
            if "Save" in save_coupon.text:
                save_string = save_coupon.text.split(" ")
                for part in save_string:
                    if "$" in part or "%" in part:
                        product_data["save_coupon"] = part
                        break

    #check if small business icon is present in the product listing and set small business status to true if it is found
    try:
        labels = search_result.find_elements(By.CSS_SELECTOR, "img.s-image")
    except NoSuchElementException:
        product_data["small_business"] = False
    
    product_data["small_business"] = False
    if labels:
        for label in labels:
            if label.get_attribute("src") == "https://m.media-amazon.com/images/I/111mHoVK0kL._SS200_.png":
                product_data["small_business"] = True
                break

    #check if bundles are available in the product listing and set bundles available status to true if they are found
    try:
        links = search_result.find_elements(By.CSS_SELECTOR, "a.a-link-normal.s-underline-text.s-underline-link-text.s-link-style")
    except NoSuchElementException:
        product_data["bundles_available"] = False
    
    if links:
        for link in links:
            if "Bundles" in link.text:
                bundles_available = True
                break
        product_data["bundles_available"] = bundles_available

    #Get the Product's URL
    try:
        href = search_result.find_element(By.CSS_SELECTOR, "a.a-link-normal.s-no-outline")
    except NoSuchElementException:
        product_data["url"] = "ERROR"

    if href:
        href = href.get_attribute("href")
        if "amazon.com" in href:
            product_data["url"] = href
        else:
            product_data["url"] = "https://www.amazon.com" + href
    else:
        product_data["url"] = "ERROR"

    try:
        #Get the Product's number of reviews    
        no_of_reviews = search_result.find_element(By.CSS_SELECTOR, "span.a-size-base.s-underline-text")
    except NoSuchElementException:
        product_data["no_of_ratings"] = "None"

    if no_of_reviews:
        product_data["no_of_ratings"] = no_of_reviews.text.replace(",", "") 
    else:
        product_data["no_of_ratings"] = "ERROR"

    product_data = get_size_stats(browser, search_result, product_data)

    return product_data
    
def create_search_result_dict():
    search_result = {
        "time": time.time(),
        "position_within_listing_type": None, 
        "ad": None,
        "listing_type": None,
        "average_rating": None,
        "no_of_ratings": None,
        "save_coupon": None,
        "bundles_available": None,
        "limited_time_deal": None,
        "amazon_choice": None,
        "best_seller": None,
        "prime": None,
        "url": None,
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
    #set the browser to headless mode [UNCOMMENT TO RUN WITH BROWSER GUI]
    #options.add_argument("-headless")

    #anti detection measures
    options.set_preference("dom.webdriver.enabled", False)
    options.set_preference("useAutomationExtension", False)
    options.binary_location = BINARY_LOCATION #locates the firefox binary

    search_term_list = [""]

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

    firefox_profile = webdriver.FirefoxProfile()
    firefox_profile.set_preference("dom.webdriver.enabled", False)
    firefox_profile.set_preference("useAutomationExtension", False)
    firefox_profile.set_preference("dom.webnotifications.enabled", False)
    firefox_profile.set_preference("dom.push.enabled", False)
    firefox_profile.set_preference("general.useragent.override", user_agent)

    browser = webdriver.Firefox(firefox_profile=firefox_profile, options=options) #opens the browser

    browser.get("https://www.amazon.com")

    captcha_solver(browser)

    total_run_time = time.time()
    unscraped_search_terms = get_unscraped_search_terms()
    for (search_term,) in unscraped_search_terms:

        network_info = subprocess.run(["mullvad", "status"], capture_output=True, text=True).stdout
        location = network_info.split("in")[-1].strip()
        mullvad_node = network_info.split(" ")[2].strip()

        print(f"[+] Connected to Mullvad node {mullvad_node} in {location}")
        print(f"[+] Scraping search term {search_term}")

        update_search_term(search_term, location, mullvad_node)

        search_bar = WebDriverWait(browser, 20).until(EC.presence_of_element_located((By.ID, "twotabsearchtextbox")))
        search_bar.clear()
        search_bar.send_keys(search_term)
        search_bar.send_keys(Keys.RETURN)

        search_results = WebDriverWait(browser, 20).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[data-component-type='s-search-result']")))
        carousels = WebDriverWait(browser, 20).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "span[data-componenet-type='s-searchgrid-carousel']")))
        video_elements = WebDriverWait(browser, 20).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[class='a-section sbv-video aok-relative sbv-vertical-center-within-parent']")))
        banner_elements = WebDriverWait(browser, 20).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[class='s-result-item s-widget s-widget-spacing-large Adholder s-flex-full-width']")))
        
        result_position = 1

        for result in search_results:
            listing_type = "Results"
            search_result = create_search_result_dict()
            search_result["listing_type"] = listing_type
            search_result["product_position"] = result_position
            search_result = get_search_result_data(browser, result, search_result)
            print(f"[+] Scraping search result {result_position}")
            insert_search_result(search_result)
            result_position += 1

        for carousel in carousels:
            if carousel.is_displayed():
                listing_type = carousel.find_element_by_xpath("./preceding-sibling::span[@class='a-size-medium-plus a-color-base']")
                carousel_products = carousel.find_elements(By.CSS_SELECTOR, "li[class^='a-carousel-card']")
                product_position = 1
                for product in carousel_products:
                    print("[+] Scraping carousel product")
                    search_result = create_search_result_dict()
                    search_result["listing_type"] = "Carousel: " + re.sub(r'\s+', '', listing_type.text)
                    ad_section_heading_keywords = ["rated", "frequently", "choice", "recommendations", "top", "our", "recommendations", "editorial", "best"]
                    if any(x in listing_type.lower() for x in ad_section_heading_keywords):
                        search_result["ad"] = True
                    search_result["positin_within_listing_type"] = product_position
                    search_result = get_search_result_data(browser, product, search_result)
                    product_position += 1
                    print("[+] Inserting carousel product")
                    insert_search_result(search_result)

        video_position = 1
        for video_element in video_elements:
            if video_element.is_displayed():
                search_result = create_search_result_dict()

                search_result["url"] = video_element.find_element(By.CSS_SELECTOR, "a[class^='a-link-normal']")["href"]
                search_result["ad"] = True
                search_result["listing_type"] = "Video" 
                search_result["position_within_listing_type"] = video_position
                search_result["amazons_choice"] = "NA"
                search_result["best_seller"] = "NA"
                search_result["prime"] = "NA"
                search_result["name"] = "NA"
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

                print("[+] Video Product completed")
                video_position += 1

        banner_position = 1
        for banner_element in banner_elements:
            if banner_element.is_displayed():
                search_result = create_search_result_dict()

                search_result["url"] = banner_element.find_element(By.CSS_SELECTOR, "a[class^='a-link-normal']")["href"]
                search_result["ad"] = True
                search_result["listing_type"] = "Banner"
                search_result["amazons_choice"] = "NA"
                search_result["best_seller"] = "NA"
                search_result["prime"] = "NA"
                search_result["name"] = "NA"
                search_result["save_coupon"] = "NA"
                search_result["limited_time_deal"] = "NA"
                search_result["bundles_available"] = "NA"
                search_result["small_business"] = "NA"
                search_result["positin_within_listing_type"] = banner_position
                search_result = get_size_stats(browser, banner_element, search_result)

                insert_search_result(search_result)
                print("[+] Banner Product completed")
                banner_position += 1

        total_run_time = time.time() - total_run_time
        print("[+] Done " + search_term + " " + str(round(total_run_time/60, 2)) + " minutes")

    browser.quit()

if __name__ == "__main__":
    main()