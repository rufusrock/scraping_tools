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
import urllib.request
from datetime import datetime
from twocaptcha import TwoCaptcha
import os
import re

FILEPATH = "C://Users//Rufus//scripts//scraping_tools//amazon-search-scraper-v2"
BINARY_LOCATION = r"C://Program Files//Mozilla Firefox//firefox.exe"
FILEPATH_TO_2CATPCHA_API_KEY = r"C://Users//Rufus//OneDrive//Desktop//credentials.txt"

#get the api key from the text file in home directory
with open(FILEPATH_TO_2CATPCHA_API_KEY, "r", encoding="UTF-8") as f:
    API_KEY = f.readline()
    f.close()

TWOCAPTCHA_API_KEY = os.getenv("APIKEY_2CAPTCHA", API_KEY)

def button_combination_count(lists):
    if not isinstance(lists, list) or not all(isinstance(sublist, list) and sublist for sublist in lists) or lists == []:
        return None
    else:
        if len(lists) == 1:
            return [(x,) for x in lists[0]]
        combs = []
        for x in button_combination_count(lists[1:]):
            for y in lists[0]:
                combs.append([y] + list(x))
        return combs
    
def option_combo_count(browser, twister):
    try:
        button_rows = browser.find_elements(By.CSS_SELECTOR, "div[id='tp-inline-twister-dim-values-container']")
        buttons = []
        for row in button_rows:
            temp_buttons = []
            for button in row.find_elements(By.CSS_SELECTOR, "input[class='a-button-input']"):
                if button.is_displayed():
                    temp_buttons.append(button)
            buttons.append(temp_buttons)

        possible_combos = button_combination_count(buttons)
        return len(possible_combos)
    except NoSuchElementException:
        buttons = []
        twister_rows = twister.find_elements(By.CSS_SELECTOR, "ul[data-action='a-button-group']")

        for row in twister_rows:
            temp_buttons = []
            for button in row.find_elements(By.CSS_SELECTOR, "span[data-action='swatchthumb-action]"):
                if button.is_displayed():
                    temp_buttons.append(button)
            buttons.append(temp_buttons)
            possible_combos = button_combination_count(buttons)
            return len(possible_combos)  

#looks for captcha and solves it
def captcha_solver(browser):
    captcha = WebDriverWait(browser, 20).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "form[action='/errors/validateCaptcha']")))
    if captcha:
        solver = TwoCaptcha(TWOCAPTCHA_API_KEY)
        try:
            print("[+] Solving Captcha")
            image_url = captcha[0].find_elements(By.TAG_NAME, "img").get_attribute("src")
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

#after product page has been loaded this scrapes key data from it
def product_page_scraper(browser, soup, product_data):
    #if the product title is none try and get the product name again
    
    name = WebDriverWait(browser, 20).until(EC.presence_of_element_located((By.ID, "productTitle")))
    if name:
        product_data["product_name"] = name.text
    else:
        product_data["product_name"] = "ERROR"
    
    s_sidebar = WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[id='corePrice_feature_div']")))
    if s_sidebar:
        product_data["current_price"] = s_sidebar.find_element(By.CSS_SELECTOR, "span[class:'a-offscreen']").text
    else:
        product_data["current_price"] = "Out of Stock"

    try:
        list_price = browser.find_element(By.CSS_SELECTOR, "span[data-a-strike='true']")
        product_data["list_price"] = list_price[0].text
    except NoSuchElementException:
        product_data["list_price"] = None

    try:
        discount = WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "span[class='a-size-large a-color-price savingPriceOverride aok-align-center reinventPriceSavingsPercentageMargin savingsPercentage']")))
        product_data["discount"] = discount.text
    except NoSuchElementException:
        product_data["discount"] = None

    try:
        best_seller_label = browser.find_element(By.CSS_SELECTOR, "span[class='a-icon a-icon-addon p13n-best-seller-badge']")
        if best_seller_label:
            product_data["best_seller_label_present"] = True
    except NoSuchElementException:
        product_data["best_seller_label_present"] = False

    try:
        amazon_choice_label = browser.find_element(By.CSS_SELECTOR, "span[class='a-size-small aok-float-left ac-badge-rectangle']")
        if "Amazon's" in amazon_choice_label and "choice" in amazon_choice_label:
            product_data["amazon_choice_label_present"] = True
    except NoSuchElementException:
        product_data["amazon_choice_label_present"] = False


    shipping_widget = browser.find_element(By.CSS_SELECTOR, "span[data-csc-c-delivery-benefit-program-id='paid_shipping']").text.split(" ")
    if shipping_widget:
        for part in shipping_widget:
            if "FREE" in part:
                product_data["shipping_price"] = True
            elif "$" in part:
                product_data["shipping_price"] = part
    else:
        product_data["shipping_price"] = "ERROR"
    
    try:
        prime_widget = browser.find_element(By.CSS_SELECTOR, "div[id='primePopoverContent]")
        product_data["prime_status"] = True
    except NoSuchElementException:
        product_data["prime_status"] = False

    try:
        product_data["seller_name"] = browser.find_elements(By.CSS_SELECTOR, "div[tabular-attribute-name='Sold by]")[1].find_element(By.CSS_SELECTOR, "span[class='a-size-small tabular-buybox-text-message]").text
    except NoSuchElementException:
        product_data["seller_name"] = "ERROR - Likely out of stock"

    try:
        product_data["shipped_by"] = browser.find_elements(By.CSS_SELECTOR, "div[tabular-attribute-name='Ships from]")[1].find_element(By.CSS_SELECTOR, "span[class='a-size small tabular-buybox-text-message']").text
    except NoSuchElementException:
        product_data["shipped_by"] = "ERROR - Likely out of stock"

    histogram_rows = browser.find_elements(By.CSS_SELECTOR, "tr[class='a-histogram-row']")
    try:
        five_star_percentage = histogram_rows[0].find_element(By.CSS_SELECTOR, "span[class='a-size-base]").a.text.replace("\n", "").replace(" ", "")
    except NoSuchElementException:
        five_star_percentage = 0
    try:
        four_star_percentage = histogram_rows[1].find_element(By.CSS_SELECTOR, "span[class='a-size-base]").a.text.replace("\n", "").replace(" ", "")
    except NoSuchElementException:
        four_star_percentage = 0
    try:
        three_star_percentage = histogram_rows[2].find_element(By.CSS_SELECTOR, "span[class='a-size-base]").a.text.replace("\n", "").replace(" ", "")
    except NoSuchElementException:
        three_star_percentage = 0
    try:
        two_star_percentage = histogram_rows[3].find_element(By.CSS_SELECTOR, "span[class='a-size-base]").a.text.replace("\n", "").replace(" ", "")
    except NoSuchElementException:
        two_star_percentage = 0
    try:
        one_star_percentage = histogram_rows[4].find_element(By.CSS_SELECTOR, "span[class='a-size-base]").a.text.replace("\n", "").replace(" ", "")
    except NoSuchElementException:
        one_star_percentage = 0

    categories = browser.find_element(By.CSS_SELECTOR, "div[id='wayfinding-breadcrumbs_feature_div']")
    #.find_elements(By.CSS_SELECTOR, "li[class='a-breadcrumb-item']")
    if "results" in categories.find_elements(By.CSS_SELECTOR, "a[class='a-link-normal a-color-tertiary']")[0].text:
        browser.refresh()
        categories = WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[id='wayfinding-breadcrumbs_feature_div']")))

    category_list = [None, None, None, None, None]
    if "results" in categories.find_elements(By.CSS_SELECTOR, "a[class='a-link-normal a-color-tertiary']")[0].text:
        category_list = ["ERROR", "ERROR", "ERROR", "ERROR", "ERROR"]
    else:
        counter = 0
        for category in categories.find_elements(By.CSS_SELECTOR, "a[class='a-link-normal a-color-tertiary']"):
            category_list[counter] = category.text.replace("\n", "").replace(" ", "")
            counter += 1

        product_data["category_1"] = category_list[0]
        product_data["category_2"] = category_list[1]
        product_data["category_3"] = category_list[2]
        product_data["category_4"] = category_list[3]
        product_data["category_5"] = category_list[4]

    try:
        twister = browser.find_element(By.CSS_SELECTOR, "div[id='twister_feature_div']")
        product_data["alternate_product_options_available"] = True
        product_data["no_possible_product_configurations"] = option_combo_count(browser, twister)
        
    except NoSuchElementException:
        product_data["alternate_product_options_available"] = False
        product_data["no_possible_product_configurations"] = None    

    return product_data

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
    
    return True

if __name__ == "__main__":
    main()

    