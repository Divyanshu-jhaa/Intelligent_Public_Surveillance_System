from flask import Flask
from flask import request
import json
from bson import json_util
from bson.objectid import ObjectId
from pymongo import MongoClient
from dotenv import load_dotenv,dotenv_values
from flask_cors import CORS
client=MongoClient("mongodb://localhost:27017")
db=client.SurveillanceDB
user_records=db.user_records
video_records=db.video_records
anomaly_records=db.anomaly_records
app=Flask(__name__)
CORS(app)
config=dotenv_values(".env")

@app.get("/")
def home():
    return "Model Server is Running!"

@app.post("/api/addVideo")
def addVideo():
    request_data_bytes = request.data
    request_data_string = request_data_bytes.decode('utf-8')
    request_data_dict = json.loads(request_data_string)  

    res=video_records.insert_one(request_data_dict)  
    return json.dumps({"acknowledged":res.acknowledged,"_id":res.inserted_id},default=str) 
  
@app.post("/api/getVideos")
def getVideos():

    video_data=[x for x in video_records.find()]
    # print(video_data)
    return json.dumps({"res":video_data},default=str)

    
    

@app.post("/api/addAnomaly")
def addAnomaly():
    request_data_bytes=request.data
    request_data_string=request_data_bytes.decode('utf-8')
    request_data_dict=json.loads(request_data_string)
 
    res=anomaly_records.insert_many(request_data_dict['data'])  
    return json.dumps({"acknowledged":res.acknowledged,"_id":res.inserted_ids},default=str) 

   
@app.post("/api/getAnomalyById")
def getAnomalyById():
    request_data_bytes=request.data
    request_data_string=request_data_bytes.decode('utf-8')
    request_data_dict=json.loads(request_data_string)
 
    res=[x for x in anomaly_records.find({"_id":ObjectId(request_data_dict['_id'])})]
    return json.dumps({"res":res},default=str)



@app.post("/api/addUser")
def addUser():
    request_data_bytes=request.data
    request_data_string=request_data_bytes.decode('utf-8')
    request_data_dict=json.loads(request_data_string)
 
    res=user_records.insert_one(request_data_dict)
    print(res.inserted_id)
    print(type(res.inserted_id))
    return json.dumps({"acknowledged":res.acknowledged,"_id":res.inserted_id},default=str)
  
@app.post("/api/authUser")
def authUser():
    request_data_bytes=request.data
    request_data_string=request_data_bytes.decode('utf-8')
    request_data_dict=json.loads(request_data_string)

    res=[x for x in user_records.find({"username":request_data_dict['username'],"password":request_data_dict['password']})]
    return json.dumps({"res":res},default=str)


