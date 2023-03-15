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
    completed_tasks.append(filename.replace("_", " "))
    
tasks = queries - completed_tasks

country = "us"
cities = ["atl", "chi", "dal", "den", "hou", "lax", "mia", "nyc", "phx", "qas","rag", "slc", "sjc", "uyk", "sea"]
#pick a random city from the lsit
import random
city = random.choice(cities)

counter = 0
query_batch = []
for query in tasks:
    if query != "search_term": 
        counter = counter + 1
        query_batch.append(query)

        if counter % 10 == 0:
            print("[+] Sending Batch of " + str(len(query_batch)) + " to Celery")
            for x in query_batch:
                print("[+] Batch contains: " + x)
            result = scraping_task.apply_async(args=[query_batch])
            query_batch = []
            print(result)
            if counter % 40 == 0:
                time.sleep(180) #tries to roughly batch the tasks into 4 (doesn't really matter because celery is async
                os.system("mullvad relay set location " + country + " " + random.choice(cities)) 

            

        
        
