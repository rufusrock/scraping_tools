from logging import addLevelName
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import urllib.request
import csv
import argparse
from time import sleep
import os
from datetime import datetime
from geopy.geocoders import Nominatim
from random import randint

header = ["COUNTRY", "DATE_RCRDED", "TIME_RCRDED", "QUERY", "SRCH_AMZN_RANK(S)", "SRCH_AMZN_YCOORDS", "NO_OF_TEXT_ADS", "AMZN_APPS_IN_TXT_ADS",  "AMZN_TXT_AD_COORDS", "GSHOP_CRSL", "GSHOP_SIDEBAR", "AMAZON_PSTN(S)_IN_GSHOP_ADS", "GMAPS_WIDGET", "TEXT_AD_DOMAINS", "TEXT_AD_Y_COORDS","GSHOP_AD_DOMAINS", "MAPS_Y_COORDS"] #13
search_term_list = ["buy shampoo"]

with open("C://Users//Rufus//OneDrive//Desktop//google_search_amazon_data_6.csv", "a", encoding="UTF8", newline="") as f: 
    writer = csv.writer(f)
    #writer.writerow(header)

    options = Options()
    options.binary_location = r'C:\Program Files\Mozilla Firefox\firefox.exe'

    browser = webdriver.Firefox(options=options)
    browser.get('http://www.google.com') 

    time.sleep(1)
    try:
        browser.find_element(By.ID,"L2AGLb").click()
        time.sleep(1)
    except:
        print("No TOS Form found")
       
    location = "England"

    for z in range(0,50):
        for search in search_term_list:
            browser.get('http://www.google.com') 
            time.sleep(1)

            element = WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.NAME, "q")))
            element.send_keys(search, Keys.RETURN)

            time.sleep(2)

            html_data = browser.page_source
            soup = BeautifulSoup(html_data, 'html.parser')
            current_time = datetime.now()
            time_rcrd = datetime.strftime(current_time, '%H:%M:%S')
            date_rcrd = datetime.strftime(current_time, '%d/%m/%y')
      

            #page_data = [search, [], [], 0, False, False, False, current_time, [], [], [], [], [], []] #13
            page_data = [location, date_rcrd, time_rcrd, search, [], [], [], [], [], False, False, [], False, [], [], [], []] #amazon_rank 4, amazon_ycoords 5, no of text ads 6, amazon appearances in text ads 7, amazon text ad y coords 8, crsl 9, sidebar 10, amazon position in gshopping 11, maps 12, text ad domains 13, text ad y coordinates 14, gshopping ad domains 15

            time.sleep(randint(0,20))

            if soup.find_all(id="taw") != []:
                ad_div = soup.find_all("a", "sVXRqc")
                if soup.find_all("g-scrolling-carousel", "pla-carousel") != []:
                    page_data[9] = True
                    carousel_ad_data = soup.find_all("a", "plantl pla-unit-single-clickable-target clickable-card")
                    carousel_ads = []
                    amazon_appearances = []
                    text_ads = []
                    amazon_appearances_in_txt_ads = []
                    text_ad_y_coords = []
          
                    for x in carousel_ad_data:
                        try:
                            carousel_ads.append(x['href'].split('/')[2])
                        except:
                            carousel_ads.append(x['href'])

                    for x in range(0,len(carousel_ads)):
                        if "amazon" in carousel_ads[x]:
                            amazon_appearances.append(x)

                    page_data[15] = carousel_ads
                    page_data[11] = amazon_appearances

                    page_data[6] = len(ad_div) # should be - nothing because the extra reference from inspector is in the style sheet
               
                    if len(ad_div) > 0: 
                        for ad in ad_div:
                            try:
                                text_ads.append(ad['href'].split('/')[2])
                            except:
                                text_ads.append(ad['href'])

                        for x in range(0,len(text_ads)):
                            if "amazon" in text_ads[x]:
                                amazon_appearances_in_txt_ads.append(x + 1)

                        page_data[13] = text_ads
                        page_data[7] = amazon_appearances_in_txt_ads

                        elements = browser.find_elements(By.CLASS_NAME,"sVXRqc")

                        for x in range(0,len(text_ads)):
                            y_relative_coord = elements[x].location['y']
                            browser_navigation_panel_height = browser.execute_script('return window.outerHeight - window.innerHeight;')
                            y_absolute_coord = y_relative_coord + browser_navigation_panel_height
                            text_ad_y_coords.append(y_absolute_coord)

                            if "amazon" in text_ads[x]:
                                page_data[8].append(y_absolute_coord)

                        page_data[14] = text_ad_y_coords


                elif soup.find_all("div", "Yi78Pd") != []:
                    page_data[10] = True
                    carousel_ad_data = soup.find_all("a", "plantl pla-unit-single-clickable-target clickable-card")
                    carousel_ads = []
                    amazon_appearances = []
                    text_ads = []
                    amazon_appearances_in_txt_ads = []
                    text_ad_y_coords = []

                    for x in carousel_ad_data:
                        try:
                            carousel_ads.append(x['href'].split('/')[2])
                        except:
                            carousel_ads.append(x['href'])

                    for x in range(0,len(carousel_ads)):
                        if "amazon" in carousel_ads[x]:
                            amazon_appearances.append(x)

                    page_data[15] = carousel_ads
                    page_data[11] = amazon_appearances


             
                    page_data[6] = len(ad_div)

                    if len(ad_div) > 0: 
                        for ad in ad_div:
                            try:
                                text_ads.append(ad['href'].split('/')[2])
                            except:
                                text_ads.append(ad['href'])

                        for x in range(0,len(text_ads)):
                            if "amazon" in text_ads[x]:
                                amazon_appearances_in_txt_ads.append(x)

                        page_data[13] = text_ads
                        page_data[7] = amazon_appearances_in_txt_ads

                        elements = browser.find_elements(By.CLASS_NAME,"sVXRqc")

                        for x in range(0,len(text_ads)):
                            y_relative_coord = elements[x].location['y']
                            browser_navigation_panel_height = browser.execute_script('return window.outerHeight - window.innerHeight;')
                            y_absolute_coord = y_relative_coord + browser_navigation_panel_height
                            text_ad_y_coords.append(y_absolute_coord)

                            if "amazon" in text_ads[x]:
                                page_data[8].append(y_absolute_coord)

                        page_data[14] = text_ad_y_coords
                   
                else:
                    page_data[6] = len(ad_div)
                    text_ads = []
                    amazon_appearances_in_txt_ads = []
                    text_ad_y_coords = []

                    if len(ad_div) > 0: 
                        for ad in ad_div:
                            text_ads.append(ad['href'].split('/')[2])


                        for x in range(0,len(text_ads)):
                            if "amazon" in text_ads[x]:
                                amazon_appearances_in_txt_ads.append(x)

                        page_data[13] = text_ads
                        page_data[7] = amazon_appearances_in_txt_ads
                
                        elements = browser.find_elements(By.CLASS_NAME,"sVXRqc")

                        for x in range(0,len(text_ads)):
                            y_relative_coord = elements[x].location['y']
                            browser_navigation_panel_height = browser.execute_script('return window.outerHeight - window.innerHeight;')
                            y_absolute_coord = y_relative_coord + browser_navigation_panel_height
                            text_ad_y_coords.append(y_absolute_coord)

                            if "amazon" in text_ads[x]:
                                page_data[8].append(y_absolute_coord)

                        page_data[14] = text_ad_y_coords
            else:
                page_data[6] = 0

            if soup.find_all("div", "o8ebK") != []:
                page_data[12] = True
                map_element = browser.find_elements(By.CLASS_NAME, "o8ebK")
                for maps in map_element:
                    y_relative_coord = maps.location['y']
                    browser_navigation_panel_height = browser.execute_script('return window.outerHeight - window.innerHeight;')
                    y_absolute_coord = y_relative_coord + browser_navigation_panel_height
                    page_data[16].append(y_absolute_coord)

            search_results = soup.find_all("div", "yuRUbf")
            elements = browser.find_elements(By.CLASS_NAME,"yuRUbf")
            counter = 0

            for element in elements:
                counter = counter + 1
                if element.is_displayed() == True: 
                    if "https://www.amazon" in element.get_attribute("innerHTML"): 
                        page_data[4].append(counter)
                        y_relative_coord = element.location['y']
                        browser_navigation_panel_height = browser.execute_script('return window.outerHeight - window.innerHeight;')
                        y_absolute_coord = y_relative_coord + browser_navigation_panel_height
                        page_data[5].append(y_absolute_coord)

        
            for x in range(0,len(page_data)):
                if page_data[x] == []:
                    page_data[x] = "None"

           
            writer.writerow(page_data)
            complete_percent = (z + 2) * 2

            #os.system('cls' if os.name == 'nt' else 'clear')
            print(str(complete_percent) + "% Complete")
        
            
    browser.quit()
    f.close()
