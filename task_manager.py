#task_distributor
from amazon_search_light import scraping_task
import time 

#open queries_file.csv and read the queries into a list

queries = []
with open('queries_file.csv', 'r', encoding="UTF-8") as f:
    for line in f:
        queries.append(line.replace("\n", ""))

#get all the file names that exist within the local_data directory
import os
files = os.listdir("local_data")

completed_tasks = []
#iterate through the queries and check if the query is already present in the local_data directory
counter = 0
for filename in files:
    filename_list = filename.split("-")
    filename_list = filename_list[4]
    filename_list = filename_list.split("_")
    del filename_list[0]
    for x in filename_list:
        x.replace("_", " ")
    filename_list = " ".join(filename_list)
    filename_list = filename_list.split(".")[0]
    final_str = "".join(filename_list)

    for query in queries:
        if final_str in query:
            completed_tasks.append(final_str)

country = "us"
cities = ["atl", "chi", "dal", "den", "hou", "lax", "mia", "nyc", "phx", "qas","rag", "slc", "sjc", "uyk", "sea"]
#pick a random city from the lsit
import random
city = random.choice(cities)

counter = 0
for query in queries:
    if query not in completed_tasks and query != "search_term" and query != "k-cup flavored coffee":
        counter = counter + 1
        
        result = scraping_task.apply_async(args=[query])
        print(result)
        time.sleep(10)

        if counter % 1 == 0:
            time.sleep(180)
            os.system("mullvad relay set location " + country + " " + random.choice(cities)) 
            time.sleep(60)
            

        
        
