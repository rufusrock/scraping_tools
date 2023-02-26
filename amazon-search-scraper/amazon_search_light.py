from selenium import webdriver
#from seleniumwire import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import ElementClickInterceptedException, NoSuchElementException
from colorama import init, Fore
from bs4 import BeautifulSoup
from random import randint
import time
import shutil
import urllib.request
from datetime import datetime
from twocaptcha import TwoCaptcha
import csv
import os
import re
from celery import Celery
import geocoder
from math import floor

# hard code this so users can change the location
# also __file__ doesn't work from the repl
FILE_PATH = "/home/brandon/scraping_tools/amazon-search-scraper"
USERNAME = "rufusrock"
# don't commit password! none of this proxy stuff is currently enabled - too expensive :(
# PASSWORD = "######"
# ENDPOINT = "us-pr.oxylabs.io:10000"
# BROKER_URL = "redis://localhost:6379/0"

BINARY_LOCATION = r"C://Program Files//Mozilla Firefox//firefox.exe"
# ubuntu: BINARY_LOCATION = "/snap/firefox/current/usr/lib/firefox/firefox-bin"
EXTENSION_FILEPATH = r"C://Users//Rufus//AppData//Roaming//Mozilla//Firefox//Profiles//ng032s5o.default-release//extensions//{44df5123-f715-9146-bfaa-c6e8d4461d44}.xpi"
# ubuntu: EXTENSION_FILEPATH = "/home/brandon/snap/firefox/common/.mozilla/firefox/0tsz0chl.default/extensions/{44df5123-f715-9146-bfaa-c6e8d4461d44}.xpi"
FILEPATH_TO_2CAPTCHA_API_KEY = r"C://Users//Rufus//OneDrive//Desktop//2captcha_api_key.txt"

#get the api key from the text file in home directory
with open(FILEPATH_TO_2CAPTCHA_API_KEY, "r", encoding="UTF-8") as f:
    API_KEY = f.readline()
    f.close()

TWOCAPTCHA_API_KEY = os.getenv("APIKEY_2CAPTCHA", API_KEY)

#Defines a function to install fakespot firefox addon and any other addons that might be required
def install_addon(self, path, temporary=None):
    # Usage: driver.install_addon('/path/to/fakespot.xpi')
    # ‘self’ refers to the “Webdriver” class
    # 'path' is absolute path to the addon that will be installed
    payload = {"path": path}
    if temporary:
        payload["temporary"] = temporary
    # The function returns an identifier of the installed addon.
    # This identifier can later be used to uninstall installed addon.
    return self.execute("INSTALL_ADDON", payload)["value"]

#Creates a new csv file with the current date and time and writes the header to it
def file_creator(header, csv_file_path):
    csv_file = open(csv_file_path, "w")
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(header)
    csv_file.close()

#Gets the users location using IP and geocoder library
def get_location(ip):
    g = geocoder.ip(ip)
    location = g.city + ", " + g.country
    print("[+]: Location: " + location)
    return location

#gets all the relevant size information about the product from the webpage
def get_size_stats(browser, element, product_data):
    if element.is_displayed() == True:
        element_size = [round(element.size["width"], 2), round(element.size["height"], 2)]
        element_area = element.size["width"] * element.size["height"]
        screen_area = browser.get_window_size()["width"] * browser.get_window_size()["height"]
        element_y_coord = round(element.location["y"], 2)
        no_of_scrolls = floor(element_y_coord /  browser.get_window_size()["height"])
        element_x_coord = round(element.location["x"],2)
        body_area = browser.find_element(By.TAG_NAME, "body").size["width"] * browser.find_element(By.TAG_NAME, "body").size["height"]
        body_percentage = round((element_area / body_area) * 100, 2)

        product_data["search_result_size"] = element_area
        product_data["search_result_window_percentage"] = round((element_area / screen_area) * 100, 2)
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

#used whilst iterating through search listings to get data from them
def get_product_data(browser, product, s_product, product_data):
    #Checks if the product is an ad
    ad = product.find_all('d', attrs={'class': lambda e: e.startswith('currentPrice') if e else False})
    if ad != [] or "sponsored" in str(product) or "Sponsored" in str(product) or "AdHolder" in str(product["class"]):
        if "Carousel" not in product_data["listing_type"]:
            product_data["listing_type"] = "Search Injected Ad"
            product_data["ad"] = True

    #get the product name
    if product.find("span", {"class": "a-size-medium a-color-base a-text-normal"}) != None:
        product_data["product_name"] = product.find("span", {"class": "a-size-medium a-color-base a-text-normal"}).text
    else:
        product_data["product_name"] = product.find("span", {"class": "a-size-base-plus a-color-base a-text-normal"}).text

    #get the product price
    product_data["current_price"] = product.find("span", {"class": "a-offscreen"}).text

    #get the product rating
    try:
        rating_list = product.find("span", {"class": "a-icon-alt"}).text.split(" ")
        for string in rating_list:
            if "." in string:
                product_data["average_rating"] = string
                break
    except:
        product_data["average_rating"] = "ERROR"

    #if there is an amazon brand logo in the listing set the amazon brand status to true 
    amazon_banner = product.find("span", {"class": "a-color-state puis-light-weight-text"})
    if amazon_banner != None:
        product_data["amazon_brand"] = True
    else:
        product_data["amazon_brand"] = False

    #if there is a prime logo in the listing set the prime search status to true
    prime_logo = product.find("i", {"class": "a-icon a-icon-prime a-icon-medium"})
    if prime_logo != None:
        product_data["prime_search_label_present"] = True
    
    #look for best seller icon in product listing and set best seller status to true if it is found   
    icon_element = product.find("span", {"class": "a-badge-label-inner a-text-ellipsis"})
    if icon_element != None:
        if "Best" in icon_element.span.text:
            product_data["best_seller_search_label_present"] = True
        elif "Amazon" in icon_element.span.text:
            product_data["amazons_choice_search_label_present"] = True
    
    #look for a limited time deal icon in the product listing and set limited time deal status to true if it is found
    limited_time_deal = product.find("span", {"data-a-badge-color": "sx-lightning-deal-red"})
    if limited_time_deal != None:
        if limited_time_deal.find("span", {"class":"a-badge-text"}).text != "":
            product_data["limited_time_deal_search_label_present"] = True
    
    #look for a save coupon icon in the product listing and set save coupon status to true if it is found
    save_coupon = product.find("span", {"class": "a-size-base s-highlighted-text-padding aok-inline-block s-coupon-highlight-color"})
    if save_coupon != None:
        if "Save" in save_coupon.text:
            save_string = save_coupon.text.split(" ")
            for part in save_string:
                if "$" in part or "%" in part:
                    product_data["save_coupon_search_label_present"] = part
                    break

    labels = product.find_all("img", {"class": "s-image"})
    for label in labels:
        if "https://m.media-amazon.com/images/I/111mHoVK0kL._SS200_.png" == label.get('src'):
            product_data["small_business"] = True

    links = product.find_all("a", {"class": "a-link-normal s-underline-text s-underline-link-text s-link-style"})
    for link in links:
        if "Bundles" in link.text:
            product_data["bundles_available"] = True

    #Get the Product's URL
    try:
        href = product.find("a",attrs={'class': lambda e: e.startswith('a-link-normal s-no-outline') if e else False}).get("href")
        if "amazon.com" in href:
            product_data["url"] = href
        else:
            product_data["url"] = "https://www.amazon.com" + href
    except:
        product_data["url"] = "Error ln 118"

    #Get the Product's number of reviews
    try:
        product_data["no_of_reviews"] = product.find("span", {"class": "a-size-base s-underline-text"}).text.replace(",", "") 
    except:
        product_data["no_of_reviews"] = "ERROR"
    
    #Gets the product's fakespot rating
    try:
        product_data["fakespot_rating"] = product.find("div", {"class": "fs-grade"}).text
    except:
        try:
            product_data["fakespot_rating"] = s_product.find_elememt(By.CLASS_NAME, "fs-grade").text
        except:
            product_data["fakespot_rating"] = "Error; ln 132"


    product_data = get_size_stats(browser, s_product, product_data)

    return product_data

#after product page has been loaded this scrapes key data from it
def product_page_scraper(browser, soup, product_data):
    #if the product title is none try and get the product name again
    try:
        name = WebDriverWait(browser, 20).until(EC.presence_of_element_located((By.ID, "productTitle")))
        product_data["product_name"] = name.text
    except:
        try: 
            product_data["product_name"] = browser.find_element(By.ID, "productTitle").text
        except:
            product_data["product_name"] = "Error; ln 156"
    
    product_data["current_price"] = get_product_price(browser) #going to have to add the bundle detection feature here and whatever else was fucking it up
   
    try:
        try:
            product_overview = soup.find("div", {"id": "productOverview_feature_div"})
            if "Amazon Basics" in str(product_overview):
                product_data["amazon_brand"] = True
        except:
            pass
        try:
            bylineinfo = soup.find("a", {"id": "bylineInfo"})
            if "Amazon" in bylineinfo.text:
                product_data["amazon_brand"] = True
        except:
            pass
    except:
        pass

    #get the average rating "div[class^='sb_add sb_adTA']")))
    rating = ""
    try:
        rating = WebDriverWait(browser, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "span[data-hook^='rating-out-of-text']")))
        if product_data["average_rating"] == "ERROR":
            product_data["average_rating"] = "[Click Required] " + rating.text.split(" ")[0]
        else:
            product_data["average_rating"] = rating.text.split(" ")[0]
    except:
        no_customer_reviews = browser.find_element(By.CSS_SELECTOR, "span[data-hook^='top-customer-reviews-title")
        if "No" in no_customer_reviews.text:
            product_data["average_rating"] = "No Customer Reviews"
        else:
            product_data["average_rating"] = "Error"

    no_reviews = ""
    #if the number of reviews is 0 or "" look for the number of reviews on this page
    if product_data["no_of_reviews"] == "0" or product_data["no_of_reviews"] == "" or product_data["no_of_reviews"] == "ERROR":
        try:
            nr = soup.find("div", {"data-hook": "total-review-count"})
            no_reviews = nr.find("span", {"class": "a-size-base a-color-secondary"}).text.split(" ")
            #find the first element in the list that contains a number
            for x in no_reviews:
                if "," in x:
                    #remove commas
                    x = x.replace(",", "")

                if x.isdigit():
                    no_reviews = x
                    break
            
            if product_data["no_of_reviews"] == "ERROR" and product_data["average_rating"] != "No Customer Reviews":
                product_data["no_of_reviews"] = "[Click Required] " + no_reviews
            elif product_data["average_rating"] == "No Customer Reviews":
                product_data["no_of_reviews"] = "0"
            else:
                product_data["no_of_reviews"] = no_reviews
        except:
            if product_data["average_rating"] == "No Customer Reviews":
                product_data["no_of_reviews"] = "0"
            else:
                product_data["no_of_reviews"] = "Error"

    #if the there is no fs grade currenlty look again on this page
    if product_data["fakespot_rating"] == "":
        fsr = WebDriverWait(browser, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[id^='fs-letter-grade-box']")))
        children = fsr.find_elements(By.TAG_NAME, "div")
        product_data["fakespot_rating"] = children[0].text

    return product_data

#Currently only used by the get_other_prices function in order to get price info from product pages - should implement solution in the product page scraper
def get_product_price(browser):
    s_sidebar = WebDriverWait(browser, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[id='corePrice_feature_div']")))
    html = browser.page_source
    soup = BeautifulSoup(html, "html.parser")
    sidebar = soup.find("div", {"id": "corePrice_feature_div"})
    try:
        price = sidebar.find("span", {"class": "a-offscreen"}).text
    except:
        price = "OutofStock"
    
    return price 

#takes the page data and saves to csv and then tries to save to cloud, throwing exception but continuing if there is any problem
def data_saver(page_data, csv_writer):
    #firstly we write the pagedata to the csv
    csv_writer.writerow(list(page_data.values()))
    #adding google cloud integration here

#gets data from carousel listing web elements and calls product page scraper once the product pages are open (clumsy implementation)
def get_carousel_data(browser, section_heading, product_data, product, s_product):
    product_data["listing_type"] = "Carousel: " + re.sub(r'\s+', '', section_heading)

    if "Rated" in section_heading or "Choice" in section_heading or "Sponsored" in str(product) or "recommendations" in section_heading or "top" in section_heading or "our" in section_heading:
        product_data["ad"] = True  
    
    product_data = get_product_data(browser, product, s_product, product_data)       
    return product_data

#gets data from video listing search results
def get_video_data(browser, s_video_element, bs4_video_element, product_data):
    #get the video link
    product_data["url"] = bs4_video_element.find("a", attrs={'class': lambda e: e.startswith('a-link-normal') if e else False})['href']

    product_data["ad"] = True
    product_data["listing_type"] = "Video Ad"
    product_data["amazons_choice_search_label_present"] = "NA"
    product_data["best_seller_search_label_present"] = "NA"
    product_data["prime_search_label_present"] = "NA"
    product_data["save_coupon_search_label_present"] = "NA"
    product_data["limited_time_deal_search_label_present"] = "NA"
    product_data["bundles_available"] = "NA"

    product_data = get_size_stats(browser, s_video_element, product_data) 
    
    #Open a new window using the product's url
    browser.execute_script("window.open('');")
    browser.switch_to.window(browser.window_handles[1])
    browser.get(product_data["url"])

    #Again uses webdriverwait to make sure the page has loaded successfully
    seleniumwait = WebDriverWait(browser, 20).until(EC.presence_of_element_located((By.ID, "productTitle")))

    temp_html = browser.page_source #gets the html of the page
    temp_soup = BeautifulSoup(temp_html, "html.parser") #parses the html

    product_data = product_page_scraper(browser, temp_soup, product_data)

    #Close the new browser window and switch back to the original window
    browser.close()
    browser.switch_to.window(browser.window_handles[0])

    return product_data

#getgs data from banner listing search results
def get_banner_data(browser, s_banner_element, bs4_banner_element, product_data):
    product_data["url"] = bs4_banner_element.find("a", attrs={'class': lambda e: e.startswith('a-link-normal') if e else False})['href']

    product_data["ad"] = True
    product_data["listing_type"] = "Banner Ad"
    product_data["amazons_choice_search_label_present"] = "NA"
    product_data["best_seller_search_label_present"] = "NA"
    product_data["prime_search_label_present"] = "NA"
    product_data["save_coupon_search_label_present"] = "NA"
    product_data["limited_time_deal_search_label_present"] = "NA"
    product_data["bundles_available"] = "NA"

    
    product_data = get_size_stats(browser, s_banner_element, product_data) 

    #Open a new window using the product's url
    browser.execute_script("window.open('');")
    browser.switch_to.window(browser.window_handles[1])
    browser.get(product_data["url"])
    #wait for the ad page to finish loading
    time.sleep(10)

    product_url = find_first_product(browser)
    browser.get(product_url)
    
    #Again uses webdriverwait to make sure the product page has loaded successfully
    seleniumwait = WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.ID, "productTitle")))
    
    temp_html = browser.page_source #gets the html of the page
    temp_soup = BeautifulSoup(temp_html, "html.parser") #parses the html

    product_data = product_page_scraper(browser, temp_soup, product_data)

    #Close the new browser window and switch back to the original window
    browser.close()
    browser.switch_to.window(browser.window_handles[0])

    return product_data

#finds the first product on an a banner ad page
def find_first_product(browser):
    #get all the a tags on the page
    a_tags = browser.find_elements(By.TAG_NAME, "a")

    #find the first a tag with an href attribute that contains the word "dp"
    for tag in a_tags:
        if tag.get_attribute("href") != None:
            if "/dp/" in tag.get_attribute("href") and "fakespot" not in tag.get_attribute("href"):
                return tag.get_attribute("href")     

#returns the current time
def get_time():
    now = datetime.now()
    time = str(now.time())
    return time

#need to get banner ads   
def init_script(search_term):
    init() #initializes the colorama library
    
    #defines how the format with which the data will be written
    sample_product = new_product("","","", "")
    header = list(sample_product.keys())

    #gets the current time and date
    now = datetime.now()
    date = now.strftime("%d-%m-%Y")
    crnttime = now.strftime("%H-%M-%S")

    print("[+]: New Instance: " + date + " " + crnttime)

    try:
        #get filepath to current python file
        file_path = os.path.dirname(os.path.realpath(__file__))
        search_term_filepath = search_term.replace(" ", "_")
        csv_file_name = "amazon_scrape_data_" + date + "_" + crnttime + "_" + search_term_filepath +".csv" #This defines the name of the csv file that will be created
        csv_file_path = file_path + "//local_data//" + csv_file_name #This defines the path to where the csv file that will be created

    except:
        csv_file_path = FILE_PATH + "//local_data//" + csv_file_name

    file_creator(header, csv_file_path) #This creates the csv file
    print("[+]: CSV file created: " + csv_file_path)

    return  csv_file_path, date, csv_file_name

#resets the product dictionary
def new_product(date, search_term, location, position_within_section):
    product_dict = {
        "date": date,
        "time": get_time(),
        "location": location,
        "search_term": search_term,
        "product_name": "",
        "ad": False,
        "listing_type": "Organic Search Result",
        "position_within_section": position_within_section,
        "url": "",
        "current_price": "",
        "fakespot_rating": "",
        "save_coupon_search_label_present": "None",
        "bundles_available": False,
        "limited_time_deal_search_label_present": False,
        "amazons_choice_search_label_present": False,
        "best_seller_search_label_present": False,
        "average_rating": "",
        "no_of_reviews": "0",
        "prime_search_label_present": False,
        "amazon_brand": False,
        "small_business": False,
        "search_result_size": "",
        "search_result_window_percentage": "",
        "search_result_html_body_percentage": "",
        "search_result_y_coord": "",
        "search_result_x_coord": "",
        "no_of_scrolls_for_product_visibility": "",        
    }
    return product_dict

""" def proxy_setup():
    wire_options = {
        'proxy': {
            "http": f"http://{USERNAME}:{PASSWORD}@{ENDPOINT}",
            "https": f"http://{USERNAME}:{PASSWORD}@{ENDPOINT}",
        },
        'mitm_http2': False
    }
    return wire_options """

def captcha_solver(browser):
    captcha = browser.find_elements(By.CSS_SELECTOR, "form[action='/errors/validateCaptcha']")
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

celery_app = Celery("scraper", broker=BROKER_URL)

os.environ.setdefault('FORKED_BY_MULTIPROCESSING', '1')

# search_term = "towel stand"
@celery_app.task
def scraping_task(search_term):
    total_run_time = time.time() #Begin the timer for the total run time of the script
    csv_file_path, date, csv_file_name = init_script(search_term) #Initializes the script

    with open(csv_file_path, "a", encoding="UTF-8", newline="") as f: #opens the csv file in append mode
        writer = csv.writer(f)
        #proxies = proxy_setup()

        options = Options()
        #set the browser to headless mode [UNCOMMENT TO RUN WITH BROWSER GUI]
        options.headless = True

        options.binary_location = BINARY_LOCATION #locates the firefox binary
        browser = webdriver.Firefox(options=options)
        time.sleep(5)

        browser.install_addon(EXTENSION_FILEPATH, temporary=True) #Installs the fakespot addon
        print("[+]: Fakespot addon installed")
        time.sleep(20) #waits for the addon to install

        browser.switch_to.window(browser.window_handles[1])
        browser.close()
        browser.switch_to.window(browser.window_handles[0])

        browser.get("https://ip.oxylabs.io/")
        ip = browser.find_element(By.CSS_SELECTOR, "pre").text
        location = get_location(ip) #Gets the location of the proxy

        browser.get("https://www.amazon.com")
        time.sleep(10)
        captcha_solver(browser)
        time.sleep(10)
        browser.refresh()
        counter = 0

        print("[+]: Now working on search term: " + search_term)
        search_bar = WebDriverWait(browser,20).until(EC.presence_of_element_located((By.ID, "twotabsearchtextbox"))) #finds the amazon search bar
        search_bar.clear() #clears the search bar
        search_bar.send_keys(search_term) #enters the search term
        search_bar.send_keys(Keys.RETURN) #presses the enter key
        
        # I got a timeout exception here
        # Page seems to have loaded fine though
        time.sleep(30)

        html = browser.page_source #gets the html of the page
        soup = BeautifulSoup(html, "html.parser") #parses the html

        bs4_products = soup.find_all("div", {"data-component-type": "s-search-result"}) #compiles a list of bs4 search result elements
        s_products = browser.find_elements(By.CSS_SELECTOR, '[data-component-type="s-search-result"]') #compiles a list of selenium search result elements

        #product_visbility_list = visibility_check(browser, s_products)

        carousels = soup.find_all("span",{"data-component-type": "s-searchgrid-carousel"})
        s_carousels = browser.find_elements(By.CSS_SELECTOR, "span[data-component-type='s-searchgrid-carousel']")
        carousel_counter = 0

        for carousel in carousels:
            print("[+] Carousel index: " + str(carousel_counter))
            #gets the carousel's heading
            section_heading = carousel.find_previous("span", {"class": "a-size-medium-plus a-color-base"}).text
            #gets a list of the carousel's products
            carousel_products = carousel.find_all("li",attrs={'class': lambda e: e.startswith('a-carousel-card') if e else False})

            if len(s_carousels) >= carousel_counter:
                s_carousel_products = s_carousels[carousel_counter].find_elements(By.CSS_SELECTOR, "li[class^='a-carousel-card']")
                #carousel_visbility_list = visibility_check(browser, s_carousel_products)
                carousel_data = []
                
                counter = 0
                for product in carousel_products: 
                    try:
                        product_data = new_product(date, search_term, location, counter + 1) #creates a new dictionary for the product
                        print("[+] Carousel Products completed: " + str(counter +1))
                        
                        product_data = get_carousel_data(browser, section_heading, product_data, product, s_carousel_products[counter])
                        data_saver(product_data, writer) #saves the data to the database and to local csv
                    except:
                        pass
                        
                    counter = counter + 1                        
            else:
                break

            carousel_counter += 1

        video_class_prefix = 'a-section sbv-video aok-relative sbv-vertical-center-within-parent'
        #get selenium video elements
        s_video_elements = browser.find_elements(By.CSS_SELECTOR,"div[class*='a-section sbv-video aok-relative sbv-vertical-center-within-parent']")
        # video_visbility_list = visibility_check(browser, s_video_elements)

        #get bs4 video elements
        video_elements = soup.find_all('div', attrs={'class': lambda e: e.startswith(video_class_prefix) if e else False})

        if video_elements != []:
            print(Fore.LIGHTYELLOW_EX + '[+] Video elements found')
            counter = 0
            for video in video_elements:
                try:
                    parent = s_video_elements[counter].find_element(By.XPATH, '..')
                    while True:
                        if "sg-row" in parent.get_attribute("class"):
                            break
                        parent = parent.find_element(By.XPATH, '..')

                    product_data = new_product(date, search_term, location, counter + 1) #creates a new dictionary for the product
                    product_data = get_video_data(browser, s_video_elements[counter], video, product_data)
                    product_data = get_size_stats(browser, parent, product_data)

                    product_index = counter
                    # Add the product's data to the list
                    data_saver(product_data, writer) #saves the data to the database and to local csv
                except:
                    try:
                        browser.switch_to.window(browser.window_handles[1])
                        browser.close()
                        browser.switch_to.window(browser.window_handles[0])
                    except:
                        pass
                    print("[-]: Error")
                    pass
                counter += 1

        
        banner_ads = soup.find_all('div', {'class': 's-result-item s-widget s-widget-spacing-large AdHolder s-flex-full-width'})
        s_banner_ads = browser.find_elements(By.CSS_SELECTOR, "div[class='s-result-item s-widget s-widget-spacing-large AdHolder s-flex-full-width']")

        if banner_ads != []:
            print(Fore.LIGHTYELLOW_EX + '[+] Banner Ads found')
            counter = 0
            for ad in banner_ads:
                try:
                    product_data = new_product(date, search_term, location, counter + 1) #creates a new dictionary for the product
                    product_data = get_banner_data(browser, s_banner_ads[counter], ad, product_data)
                    data_saver(product_data, writer) #saves the data to the database and to local csv
                except:
                    try:
                        browser.switch_to.window(browser.window_handles[1])
                        browser.close()
                        browser.switch_to.window(browser.window_handles[0])
                    except:
                        pass
                    print("[-]: Error")
                    pass
            
                counter+=1
        
        counter = 0
        
        for product in bs4_products:
            
            section_heading = "Results" #Everything here is a result

            try:
                print("[+] Product Iteration Completion Status: " + str(counter + 1) + "/" + str(len(bs4_products)))

                product_data = new_product(date, search_term, location, counter + 1) #creates a new dictionary for the product

                product_data = get_product_data(browser, product, s_products[counter], product_data) #gets the data for the product

                if product_data["average_rating"] == "ERROR":
                        #Open a new window using the product's url
                    browser.execute_script("window.open('');")
                    browser.switch_to.window(browser.window_handles[1])
                    browser.get(product_data["url"])
                    #Again uses webdriverwait to make sure the page has loaded successfully
                    seleniumwait = WebDriverWait(browser, 20).until(EC.presence_of_element_located((By.ID, "productTitle")))

                    temp_html = browser.page_source #gets the html of the page
                    temp_soup = BeautifulSoup(temp_html, "html.parser") #parses the html

                    product_data = product_page_scraper(browser, temp_soup, product_data)

                    #Close the new browser window and switch back to the original window
                    browser.close()
                    browser.switch_to.window(browser.window_handles[0])
                    time.sleep(5)

                #product_page_data = product_page_scraper(browser, temp_soup, product_data) #gets the data from the product page

                data_saver(product_data, writer) #saves the data to the database and to local csv
            except:
                try:
                    browser.switch_to.window(browser.window_handles[1])
                    browser.close()
                    browser.switch_to.window(browser.window_handles[0])
                except:
                    pass
                print("[-]: Error")
                pass
            
            counter += 1

        #exit the browser
        browser.quit()
        f.close() 
        #copy the csv file to dropbox
        try:
            shutil.copyfile(csv_file_path, 'C:\\Users\\Rufus\\Dropbox\\Amazon_Scrape_1\\' + csv_file_name)
        except:
            print("[-] Error copying file to dropbox")

        total_run_time = time.time() - total_run_time
        end_string = "[+] Done " + search_term + " " + str(round(total_run_time/60, 2)) + " minutes"
        return end_string


#Rufus_Rock, 2022
