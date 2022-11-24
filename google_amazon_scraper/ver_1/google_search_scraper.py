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
from datetime import date

#Optional command line single search term specification:
#parser = argparse.ArgumentParser() 
#parser.add_argument("-q", "--query", help="Google Search Query")
#args = parser.parse_args()

search_term_list = []
#header = ["non_carousel_ads_present", "carousel present", "google maps present", "search query", "amazon_ranking(s)", "amazon y-coordinate"]
header = ["QUERY", "AMZN_RANK(S)", "AMZN-YCOORDS", "ADWORD_ADS","GSHOP_CRSL", "GMAPS_WIDGET", "DATE_RECORDED"]

with open("C://Users//Rufus//OneDrive//Desktop//search_terms.txt", "r") as word_file:
    for line in word_file:
       for word in line.split():
            search_term_list.append(word) 

combined_data = []

with open("C://Users//Rufus//OneDrive//Desktop//google_search_amazon_data.csv", "a", encoding="UTF8", newline="") as f: 
    writer = csv.writer(f)
    writer.writerow(header)

    options = Options()
    options.binary_location = r'C:\Program Files\Mozilla Firefox\firefox.exe'

    browser = webdriver.Firefox(options=options)
    browser.get('http://www.google.com') 

    time.sleep(1)
    browser.find_element(By.ID,"L2AGLb").click()
    time.sleep(1)

    for search in search_term_list:
        browser.get('http://www.google.com') 
        time.sleep(1)

        element = WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.NAME, "q")))
        element.send_keys(search, Keys.RETURN)

        time.sleep(2)

        html_data = browser.page_source
        soup = BeautifulSoup(html_data, 'html.parser')
        today = date.today()

        page_data = [search, [], [], 0, False, False, today]
     
        
        if soup.find_all(id="taw") != []:
            ad_div = soup.find(id="tads")
            if soup.find_all("g-scrolling-carousel", "pla-carousel") != []:
                page_data[4] = True
                try:
                    page_data[3] = len(ad_div.contents) - 2
                except:
                    page_data[3] = 0
            else:
                page_data[4] = False  
                try:
                    page_data[3] = len(ad_div.contents) - 1
                except:
                    page_data[3] = 0
       

        if soup.find_all(id="Odp5De") != []:
            page_data[5] = True

        search_results = soup.find_all("div", "yuRUbf")
        elements = browser.find_elements(By.CLASS_NAME,"yuRUbf")

        for x in range(0,len(elements)):
            if elements[x].is_displayed() == True:
                try: 
                    if "amazon" in search_results[x].a["href"]: 
                        page_data[1].append(x)
                        y_relative_coord = elements[x].location['y']
                        browser_navigation_panel_height = browser.execute_script('return window.outerHeight - window.innerHeight;')
                        y_absolute_coord = y_relative_coord + browser_navigation_panel_height
                        page_data[2].append((y_absolute_coord))

                except:
                    page_data.append("INDEX ERROR")

        combined_data.append(page_data)
        
             
    writer.writerows(combined_data)
    time.sleep(10)
    browser.quit()
    f.close()
