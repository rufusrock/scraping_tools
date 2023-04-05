#task_distributor
from amazon_search_light import scraping_task
import time 
import random
import os

#open queries_file.csv and read the queries into a list
query_counts = {}
with open('queries_file.csv', 'r', encoding="UTF-8") as f:
    for line in f:
        query = line.replace("\n", "")
        if query in query_counts:
            query_counts[query] += 1
        else:
            query_counts[query] = 1

queries = list(query_counts.keys())

# Identify and output duplicate queries
duplicates = [query for query, count in query_counts.items() if count > 1]
print("[+] Number of duplicates " + str(len(duplicates)))

#remove dupes by converting list into set and back
queries = list(set(queries))

#get all the file names that exist within the local_data directory
files = os.listdir("local_data")

completed_tasks = []
#iterate through the queries and check if the query is already present in the local_data directory
counter = 0

for filename in files:
    filename = filename.replace("_", " ")
    filename = filename.replace(".csv", "")
    if filename in queries:
        completed_tasks.append(filename)

tasks = []
todo_counter = 0

print("[+] TOTAL QUERIES: " + str(len(queries)))

for x in queries:
    if x not in completed_tasks:
        tasks.append(x)
        todo_counter +=1
    
completed_counter = len(completed_tasks)
print("[+] Completed Tasks: " + str(completed_counter))
print("[-] TODO Tasks: " + str(todo_counter))

country = "us"
cities = ["atl", "chi", "dal", "den", "hou", "lax", "mia", "nyc", "phx", "qas","rag", "slc", "sjc", "uyk", "sea"]

counter = 0
query_batch = []
threads = 4
batch_size = 4

while todo_counter > 0:
    for query in tasks:
        if query != "search_term": 
            counter = counter + 1
            query_batch.append(query)

            if counter % batch_size == 0:
                print("[+] Sending Batch of " + str(len(query_batch)) + " to Celery")
                for x in query_batch:
                    print("[+] Batch contains: " + x)
                result = scraping_task.apply_async(args=[query_batch])
                query_batch = []
                print(result)
                if counter % (batch_size * threads) == 0:
                    todo_counter = todo_counter - (batch_size * threads)
                    completed_counter = completed_counter + (batch_size * threads)
                    print("[+] Completed Tasks: " + str(completed_counter))
                    print("[-] TODO Tasks: " + str(todo_counter))
                    for z in range(0, 2):
                        time.sleep(100) #tries to roughly batch the tasks into 4 (doesn't really matter because celery is async
                        os.system("mullvad relay set location " + country + " " + random.choice(cities))

                    

            
        
