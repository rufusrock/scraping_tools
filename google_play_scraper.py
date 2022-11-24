from bs4 import BeautifulSoup
import urllib.request
import csv
import argparse
from time import sleep
import os

word_list = []

#with open("C://Users//Rufus//OneDrive//Desktop//app_search_terms.txt", "r") as word_file:
#    for line in word_file:
#        for word in line.split():
#            word_list.append(word)

header = ["result_ranking", "search query", "app_name", "publisher", "play store suffix", "appbrain link", "rating", "no. of downloads", "last_update", "Tags"]

with open("C://Users//Rufus//OneDrive//Desktop//testing.csv", "a", encoding="UTF8", newline="") as f: 
    writer = csv.writer(f)
    #writer.writerow(header)

    parser = argparse.ArgumentParser()
    parser.add_argument("-q", "--query", help="Play Store Search Query")
    args = parser.parse_args()

    word_list.append(args.query)

    for word in word_list:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("Now retrieving: " + word)
        
        play_store_link = "https://play.google.com/store/search?q=" + word + "&c=apps&hl=en&gl=US"
        data = urllib.request.urlopen(play_store_link)
        html_data = data.read().decode("utf-8")
        data.close()

        soup = BeautifulSoup(html_data, 'html.parser')

        list_items = soup.find_all(role="listitem")
        link_containers = soup.find_all("a","Si6A0c Gy4nib")
        name_containers = soup.find_all("span", "DdYX5")
        publisher_containers = soup.find_all("span", "wMUdtb")
        rating_containers = soup.find_all("span", "w2kbF")

        data = []
        appbrain_link_names = []
        appbrain_reformatted_names = []
        appbrain_links = []

        for x in range(0,len(link_containers)):
            appbrain_link_names.append(link_containers[x].get('href').split("=")[1])
            appbrain_reformatted_names.append(name_containers[x].string.replace(" ","_").lower())
            appbrain_links.append("https://www.appbrain.com/app/" + appbrain_reformatted_names[x] + "/" + appbrain_link_names[x])


        for x in range(0,len(name_containers)):
            try: 
                temp_data = urllib.request.urlopen("https://play.google.com" + link_containers[x].get('href'))
                temp_html_data = temp_data.read().decode("utf-8")
                temp_data.close()
                temp_soup = BeautifulSoup(temp_html_data, 'html.parser')

                download_estimate = temp_soup.find_all("div","ClM7O")
                last_update = temp_soup.find_all("div", "xg1aie")
                app_tags = temp_soup.find_all("a", "WpHeLc VfPpkd-mRLv6 VfPpkd-RLmnJb")

                tag_string = ""

                del app_tags[-1]
                for tag in app_tags:
                    tag_string = tag_string + tag.get('aria-label') + ", "

                print(str(x / len(name_containers) * 100) + "% Complete" )

                if "$" in rating_containers[x].string:
                    del rating_containers[x]

                data.append([x + 1, word, name_containers[x].string, publisher_containers[x].string, link_containers[x].get('href'), appbrain_links[x], rating_containers[x].string, download_estimate[1].string, last_update[0].string, tag_string])
            except:
                print("Error with: " + name_containers[x].string)

        writer.writerows(data)

print("File Updated")