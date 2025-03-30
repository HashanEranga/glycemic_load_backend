import os
import pandas as pd
from pymongo import MongoClient
from pydantic import BaseModel
from typing import Dict
from dotenv import load_dotenv

class InputData(BaseModel):
    foodName: str
    portionSize: float
    nutrients: Dict[str, float]

env_file = ".env"
if os.path.exists(env_file):
    load_dotenv(env_file)
    print(f"Loaded environment variables from {env_file}")
else:
    print(f"Error: {env_file} file not found!")
    exit(1)

MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME")
COLLECTION_NAME = os.getenv("COLLECTION_NAME") 

if not all([MONGO_URI, DATABASE_NAME, COLLECTION_NAME]):
    print("Error: Missing required environment variables!")
    exit(1)

try:
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    print("Connected to MongoDB successfully!")
except Exception as e:
    print(f"Failed to connect to MongoDB: {e}")

csv_file = "all_foods.csv"  
df = pd.read_csv(csv_file)
df = df.drop(columns=["Research Paper", "link", "Reference"])

data_list = []
for _, row in df.iterrows():
    if row.isna().any():
        print(f"Row {_} has missing values: {row[row.isna()]}")
    else:
        food_name = row["food item"]
        nutrients = {
            "carbs": float(row["Available Carbohydrate"]),
            "fats": float(row["Total Protein"]),
            "protein": float(row["Total Fat"]),
            "fiber": float(row["Total dietary fibre"])
        }
        gl = float(row["GI"])

        record = {
            "foodName": food_name,
            "nutrients": nutrients,
            "glycemicLoad": gl,
        }

        data_list.append(record)

if data_list:
    collection.insert_many(data_list)
    print(f"Inserted {len(data_list)} records into MongoDB successfully!")
else:
    print("No valid records to insert.")
