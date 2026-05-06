import urllib.request
import json
import sys
import os

# Add the root path so we can import logging_middleware
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from logging_middleware.logger import logger

DEPOT_API = "http://20.207.122.201/evaluation-service/depots"
VEHICLES_API = "http://20.207.122.201/evaluation-service/vehicles"

FALLBACK_DEPOTS = [
    { "ID": 1, "MechanicHours": 60 },
    { "ID": 2, "MechanicHours": 135 },
    { "ID": 3, "MechanicHours": 188 },
    { "ID": 4, "MechanicHours": 97 },
    { "ID": 5, "MechanicHours": 164 }
]

FALLBACK_VEHICLES = [
    { "TaskID": "264e638f-1c7a-4d67-9f9c-53f3d1766d37", "Duration": 1, "Impact": 5 },
    { "TaskID": "73ce9dca-1536-4a7a-9f1e-c67083afad61", "Duration": 6, "Impact": 2 },
    { "TaskID": "4b6e22ee-b4ed-45a4-a6af-5294b0d69f37", "Duration": 1, "Impact": 3 },
    { "TaskID": "d6372f32-852b-46a9-8e8c-e730fecc3c22", "Duration": 5, "Impact": 5 },
    { "TaskID": "ec40b581-bdfc-43e0-a047-871fdefe8167", "Duration": 7, "Impact": 3 },
    { "TaskID": "fb1e3165-67c9-4e96-a5c3-2d20085d293b", "Duration": 6, "Impact": 3 },
    { "TaskID": "330065c0-3815-4e10-a18a-b93b117e30a8", "Duration": 5, "Impact": 1 },
    { "TaskID": "72a91abc-4ed7-492c-9e99-348e7437953b", "Duration": 5, "Impact": 9 },
    { "TaskID": "8a7ff5b1-335c-4a2f-96d8-09c4a362e781", "Duration": 6, "Impact": 10 },
    { "TaskID": "08d00114-9506-463d-ba2e-3343ec4e2e89", "Duration": 6, "Impact": 6 },
    { "TaskID": "a1e0b8e6-1076-4a2f-b83b-5e6017900033", "Duration": 6, "Impact": 1 },
    { "TaskID": "52635341-7c5f-475a-9839-4676f8fe5fd4", "Duration": 1, "Impact": 5 },
    { "TaskID": "9e08defa-7bb5-4a83-9e29-417165922894", "Duration": 6, "Impact": 9 },
    { "TaskID": "f92b0f39-35ec-47c3-a465-3e49c22185b6", "Duration": 2, "Impact": 5 },
    { "TaskID": "65c0d74a-82ef-4fcc-9d85-9b082bb85310", "Duration": 5, "Impact": 7 },
    { "TaskID": "68ee2f8d-4145-4472-bce9-1d0968a8092a", "Duration": 1, "Impact": 1 },
    { "TaskID": "8a294532-c7ee-4e19-803d-f98b7e73e8bc", "Duration": 8, "Impact": 7 },
    { "TaskID": "18c655b2-380d-4295-8905-863f0de32c8f", "Duration": 2, "Impact": 9 },
    { "TaskID": "436e87a6-2b5b-42b9-9c35-deaa2c8ef54e", "Duration": 2, "Impact": 3 },
    { "TaskID": "0a823f1b-03c3-4722-af40-e17a7b9ee0ff", "Duration": 2, "Impact": 5 },
    { "TaskID": "0bf780cb-1099-4f61-99bf-dec95a7063b6", "Duration": 3, "Impact": 10 },
    { "TaskID": "e716fb11-1064-4db7-9d76-06d19f4f6f67", "Duration": 5, "Impact": 5 },
    { "TaskID": "60586e47-ab9c-407d-85ca-1215084f3f41", "Duration": 8, "Impact": 8 },
    { "TaskID": "08635e52-dad5-4b78-8ab1-e55db53c0c18", "Duration": 8, "Impact": 5 },
    { "TaskID": "871ddcf5-0bba-4233-bf12-c776c496e314", "Duration": 7, "Impact": 10 },
    { "TaskID": "b57f17dc-db77-42bf-a7e9-8fec596ce498", "Duration": 7, "Impact": 1 },
    { "TaskID": "1d893de7-fbba-4c77-927b-e3076fe805d5", "Duration": 1, "Impact": 8 },
    { "TaskID": "1743e1b5-9dfd-450b-9905-98c3e054aee1", "Duration": 5, "Impact": 8 },
    { "TaskID": "48851915-eaf5-48ec-a20c-5074d7050c5f", "Duration": 8, "Impact": 8 },
    { "TaskID": "7d81e6ca-8f03-4c4a-9ec0-701f820c5655", "Duration": 7, "Impact": 8 }
]

def fetch_data(url, fallback):
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            logger.info(f"Successfully fetched data from {url}")
            return data
    except Exception as e:
        logger.error(f"Failed to fetch from {url}: {e}. Using fallback data.")
        return fallback

def maximize_impact(vehicles, capacity):
    # This is the 0/1 Knapsack problem
    n = len(vehicles)
    dp = [[0 for _ in range(capacity + 1)] for _ in range(n + 1)]
    
    for i in range(1, n + 1):
        for w in range(1, capacity + 1):
            dur = vehicles[i-1]["Duration"]
            imp = vehicles[i-1]["Impact"]
            if dur <= w:
                dp[i][w] = max(imp + dp[i-1][w-dur], dp[i-1][w])
            else:
                dp[i][w] = dp[i-1][w]
                
    # Traceback to find selected vehicles
    res = dp[n][capacity]
    w = capacity
    selected = []
    
    for i in range(n, 0, -1):
        if res <= 0:
            break
        if res == dp[i-1][w]:
            continue
        else:
            selected.append(vehicles[i-1])
            res -= vehicles[i-1]["Impact"]
            w -= vehicles[i-1]["Duration"]
            
    return dp[n][capacity], selected

def schedule_maintenance():
    depots_data = fetch_data(DEPOT_API, {"depots": FALLBACK_DEPOTS})
    vehicles_data = fetch_data(VEHICLES_API, {"vehicles": FALLBACK_VEHICLES})
    
    depots = depots_data.get("depots", [])
    vehicles = vehicles_data.get("vehicles", [])
    
    if not depots or not vehicles:
        logger.warning("Missing depot or vehicle data")
        return
        
    for depot in depots:
        budget = depot["MechanicHours"]
        depot_id = depot["ID"]
        logger.info(f"Processing Depot {depot_id} with budget {budget} hours")
        
        max_impact, selected_vehicles = maximize_impact(vehicles, budget)
        
        print(f"\n--- DEPOT {depot_id} MAINTENANCE SCHEDULE ---")
        print(f"Daily Budget: {budget} hours")
        print(f"Maximized Impact Score: {max_impact}")
        print(f"Vehicles Scheduled: {len(selected_vehicles)}")
        total_duration = sum(v["Duration"] for v in selected_vehicles)
        print(f"Total Time Scheduled: {total_duration} hours")
        print("Tasks to perform:")
        for v in selected_vehicles:
            print(f"  - TaskID: {v['TaskID']} | Duration: {v['Duration']}h | Impact: {v['Impact']}")
        print("------------------------------------------")

if __name__ == "__main__":
    logger.info("Starting Vehicle Maintenance Scheduler...")
    schedule_maintenance()
