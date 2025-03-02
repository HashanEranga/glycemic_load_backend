import joblib
import numpy as np
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Dict
from pymongo import MongoClient
from fastapi.middleware.cors import CORSMiddleware

loaded_model = joblib.load('random_forest_model.pkl')

MONGO_URI = "mongodb+srv://glycemicLoadMongo:qazQAZ@glycemicloadmongo.pckj1.mongodb.net/admin?appName=glycemicLoadMongo&retryWrites=true&loadBalanced=false&replicaSet=atlas-8bz6ha-shard-0&readPreference=primary&srvServiceName=mongodb&connectTimeoutMS=10000&w=majority&authSource=admin&authMechanism=SCRAM-SHA-1"
DATABASE_NAME = "glycemicLoad_db"
COLLECTION_NAME = "glycemicLoad_predictions"

client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  # Allow Angular local development
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

class InputData(BaseModel):
    foodName: str
    portionSize: float
    nutrients: Dict[str, float]

@app.post("/predict/")
def predict(input_data: InputData):
    try:
        dividing_factor = input_data.portionSize/100
        X_input = np.array(list(input_data.nutrients.values()))
        X_input = X_input/dividing_factor
        prediction = loaded_model.predict([X_input])[0].round(2)

        record = {
            "foodName": input_data.foodName,
            "portionSize": input_data.portionSize,
            "nutrients": input_data.nutrients,
            "glycemicLoad": prediction,
        }
        collection.insert_one(record)

        return {"foodName": input_data.foodName, "glycemicLoad": prediction}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/retrieve/")
def retrieve(foodName: str):
    try:
        all_records = list(collection.find({}, {"_id": 0}))

        filtered_results = [record for record in all_records if foodName.lower() in record["foodName"].lower()]

        if not filtered_results:
            raise HTTPException(status_code=404, detail="No records found")

        return {"results": filtered_results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/retrieve/all")
def retrieve_all():
    try:
        results = list(collection.find({}, {"_id": 0}))
        if not results:
            raise HTTPException(status_code=404, detail="No records found")

        return {"results": results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))