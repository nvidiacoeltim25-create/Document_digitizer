from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict
import pymongo
import os
import sys
import base64
from deepface import DeepFace
import uvicorn
import time
from tensorflow.keras.applications.resnet50 import ResNet50, preprocess_input
from tensorflow.keras.preprocessing import image
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from bson.objectid import ObjectId


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models.models import CompareModel
from utils.utils import get_attachment_name
from utils.constants import FACE_SIGN_ML_PORT, MONGO_URL, attachments_folder

# MongoDB connection details
client = pymongo.MongoClient(MONGO_URL)
db = client["email_database"]
attachments_collection = db["attachments"]

# Folder where attachments are stored
os.makedirs(attachments_folder, exist_ok=True)

# FastAPI instance
app = FastAPI()

origins = ['*']

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Function to get image embedding
base_model = ResNet50(weights='imagenet', include_top=False, pooling='avg')
def get_image_embedding(img_path):
    img = image.load_img(img_path, target_size=(224, 224))
    img_data = image.img_to_array(img)
    img_data = np.expand_dims(img_data, axis=0)
    img_data = preprocess_input(img_data)
    embedding = base_model.predict(img_data)
    return embedding.flatten()

# Function to compare face images
def face_similarity_matching(img_path_1: str, img_path_2: str) -> Dict[str, str]:
    start_time = time.time()
    result = DeepFace.verify(img_path_1, img_path_2)
    similarity_score = round((1 - result['distance']), 4)
    end_time = time.time()
    time_taken = str(round((end_time - start_time), 4)) + " seconds"
    return {
        "similarity_score": str(similarity_score),
        "time_taken": time_taken
    }

# Function to compare signature images
def similarity_matching(img_path_1: str, img_path_2: str) -> float:
    embedding1 = get_image_embedding(img_path_1)
    embedding2 = get_image_embedding(img_path_2)
    similarity = cosine_similarity([embedding1], [embedding2])
    return float(similarity)  # Convert numpy.float64 to float before returning

# Endpoint to compare face images
@app.post("/compare_face")
def compare_face_images(object_ids: CompareModel) -> Dict[str, str]:
    try:
        attachment_name_1 = get_attachment_name(object_ids.object_id_1)
        attachment_name_2 = get_attachment_name(object_ids.object_id_2)
        
        if "An error occurred" in attachment_name_1 or "Attachment not found" in attachment_name_1:
            raise HTTPException(status_code=404, detail=attachment_name_1)
        
        if "An error occurred" in attachment_name_2 or "Attachment not found" in attachment_name_2:
            raise HTTPException(status_code=404, detail=attachment_name_2)
        
        file_path_1 = os.path.join(attachments_folder, attachment_name_1)
        file_path_2 = os.path.join(attachments_folder, attachment_name_2)
        
        if not os.path.exists(file_path_1):
            raise HTTPException(status_code=404, detail="File 1 not found")
        
        if not os.path.exists(file_path_2):
            raise HTTPException(status_code=404, detail="File 2 not found")
        
        result = face_similarity_matching(file_path_1, file_path_2)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Endpoint to compare signature images
@app.post("/compare_signature")
def compare_signature_images(object_ids: CompareModel) -> Dict[str, str]:
    try:
        attachment_name_1 = get_attachment_name(object_ids.object_id_1)
        attachment_name_2 = get_attachment_name(object_ids.object_id_2)
        
        if "An error occurred" in attachment_name_1 or "Attachment not found" in attachment_name_1:
            raise HTTPException(status_code=404, detail=attachment_name_1)
        
        if "An error occurred" in attachment_name_2 or "Attachment not found" in attachment_name_2:
            raise HTTPException(status_code=404, detail=attachment_name_2)
        
        file_path_1 = os.path.join(attachments_folder, attachment_name_1)
        file_path_2 = os.path.join(attachments_folder, attachment_name_2)
        
        if not os.path.exists(file_path_1):
            raise HTTPException(status_code=404, detail="File 1 not found")
        
        if not os.path.exists(file_path_2):
            raise HTTPException(status_code=404, detail="File 2 not found")
        
        start_time = time.time()
        similarity_score = similarity_matching(file_path_1, file_path_2)
        similarity_score = round(float(similarity_score), 4)  # Convert numpy.float64 to float before rounding
        end_time = time.time()
        time_taken = str(round((end_time - start_time), 4)) + " seconds"
        return {
            "similarity_score": str(similarity_score),
            "time_taken": time_taken
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=FACE_SIGN_ML_PORT)