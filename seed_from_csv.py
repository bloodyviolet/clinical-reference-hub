import csv
import requests

API_URL = "http://127.0.0.1:8000/sae/"
CSV_FILE = "nanda.csv"

# Open and read the CSV file
with open(CSV_FILE, mode='r', encoding='utf-8') as file:
    reader = csv.DictReader(file)
    
    # Loop through each row in the spreadsheet
    for row in reader:
        # The CSV headers match our API payload perfectly
        response = requests.post(API_URL, json=row)
        
        if response.status_code == 200:
            print(f"Successfully added NANDA: {row['code']}")
        else:
            print(f"Failed to add {row['code']}: {response.text}")
