import os
import joblib
import numpy as np
from fastapi import APIRouter, FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Dict
from pymongo import MongoClient
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

file_path = 'models/random_forest_model.pkl'
if os.path.exists(file_path):
    print("File exists, loading the model...")
    loaded_model = joblib.load(file_path)
else:
    print("Error: File not found!")

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
GLYCEMIC_INDEX_COLLECTION = os.getenv("GLYCEMIC_INDEX_COLLECTION")

if not all([MONGO_URI, DATABASE_NAME, COLLECTION_NAME, GLYCEMIC_INDEX_COLLECTION]):
    print("Error: Missing required environment variables!")
    exit(1)

try:
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    glycemic_index_collection = db[GLYCEMIC_INDEX_COLLECTION]
    print("Connected to MongoDB successfully!")
except Exception as e:
    print(f"Failed to connect to MongoDB: {e}")

app = FastAPI()
router = APIRouter(prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)

class InputData(BaseModel):
    foodName: str
    portionSize: float
    nutrients: Dict[str, float]

@router.post("/predict/")
def predict(input_data: InputData):
    try:
        nutritient_factor = input_data.portionSize / 100
        X_input = np.array(list(input_data.nutrients.values()))
        X_input = X_input
        prediction = loaded_model.predict([X_input])[0].round(2)
        prediction_per_food_portion = prediction * nutritient_factor

        record = {
            "foodName": input_data.foodName,
            "portionSize": input_data.portionSize,
            "nutrients": input_data.nutrients,
            "glycemicLoad": prediction_per_food_portion,
        }
        collection.insert_one(record)

        return {"foodName": input_data.foodName, "glycemicLoad": prediction_per_food_portion}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/retrieve/")
def retrieve(foodName: str):
    try:
        all_records = list(collection.find({}, {"_id": 0}))

        filtered_results = [record for record in all_records if foodName.lower() in record["foodName"].lower()]

        if not filtered_results:
            raise HTTPException(status_code=404, detail="No records found")

        return {"results": filtered_results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/retrieve/all")
def retrieve_all():
    try:
        results = list(collection.find({}, {"_id": 0}))
        if not results:
            raise HTTPException(status_code=404, detail="No records found")

        return {"results": results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/glycemicIndex/retrieve/all")
def glycemicIndex_retrieve_all():
    try:
        results = list(glycemic_index_collection.find({}, {"_id":0}))
        if not results:
            raise HTTPException(status_code=404, detail="No records found")
        return {"results": results}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/glycemicIndex/retrieve/")
def glycemicIndex_retrieve(foodName: str):
    try:
        all_records = list(glycemic_index_collection.find({}, {"_id": 0}))

        filtered_results = [record for record in all_records if foodName.lower() in record["foodName"].lower()]

        if not filtered_results:
            raise HTTPException(status_code=404, detail="No records found")

        return {"results": filtered_results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/mix-meal/retrieve/")
def mixMeal_retrieve(foodName: str):
    try:
        all_records_from_saved = list(collection.find({}, {"_id": 0}))
        all_records_from_glycemicIndex = list(glycemic_index_collection.find({}, {"_id": 0}))

        all_records = all_records_from_saved + all_records_from_glycemicIndex

        filtered_results = [record for record in all_records if foodName.lower() in record["foodName"].lower()]

        if not filtered_results:
            raise HTTPException(status_code=404, detail="No records found")

        return {"results": filtered_results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

app.include_router(router)