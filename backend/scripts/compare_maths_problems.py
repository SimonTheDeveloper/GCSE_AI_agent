import requests
import json

# Load problems from mathProblems.json
with open('/Users/simonneumann/code/GCSE_AI_agent/frontend/src/test_data/mathProblems.json', 'r') as f:
    file_problems = json.load(f)

# Fetch problems from backend API
API_URL = "http://localhost:8000/api/v1/topics/1/cards"
TOPIC_ID = "math"  # Replace with your actual topic ID

response = requests.get(API_URL.format(topic_id=TOPIC_ID))
response.raise_for_status()
db_data = response.json()
db_problems = db_data.get('cards', [])

# Compare by id
file_ids = {p['id'] for p in file_problems}
db_ids = {p['id'] for p in db_problems}

missing_in_db = file_ids - db_ids
missing_in_file = db_ids - file_ids

print("Problems in file but missing in DB:", missing_in_db)
print("Problems in DB but missing in file:", missing_in_file)

# Compare content for matching ids
for fp in file_problems:
    dbp = next((p for p in db_problems if p['id'] == fp['id']), None)
    if dbp and fp != dbp:
        print(f"Difference for problem id {fp['id']}:")
        print("File:", fp)
        print("DB:", dbp)