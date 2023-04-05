#csv amalgamator 
import csv
import os

#iterate through a list of csv files, stripping the header and appending the data to a new csv file
def csv_amalgamator(file_list, output_file):
    with open(output_file, 'w', newline='', encoding="UTF-8") as f:
        writer = csv.writer(f)
        for file in file_list:
            print(file)
            with open(file, 'r', encoding="UTF-8") as f:
                reader = csv.reader(f)
                for row in reader:
                    if "search_term" not in row and row != "":
                        writer.writerow(row)

def get_file_list(file_path):
        #get all the files in the directory and append their full paths
        files = os.listdir(file_path)
        files = [file for file in files if ".csv" in file]
        files = [file_path + "//" + file for file in files]

        return files
    
def main():
    #take a file path as input and return a list of all the files within that directory
    file_path = "C://Users//Rufus//scripts//scraping_tools//amazon-search-scraper//local_data"
    file_list = get_file_list(file_path)

    #create a newfile in the directory with the script
    output_file = "amalgamated_data.csv"
    csv_amalgamator(file_list, output_file)
    print("[+] New CSV file created: " + output_file)

if __name__ == "__main__":
    main()