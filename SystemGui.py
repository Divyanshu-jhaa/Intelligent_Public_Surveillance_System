import tkinter as tk
from tkinter import messagebox
import threading
import tensorflow as tf
import numpy as np
import json
import cv2
from datetime import datetime
import requests
import base64
from server import db
from server import client
from bson.objectid import ObjectId
import time
import gridfs
from pymongo import MongoClient
#LRCN model Variables
IMAGE_HEIGHT , IMAGE_WIDTH = 200, 100
SEQUENCE_LENGTH = 20
CLASSES_LIST = ["Explosion", "Fighting", "Robbery","RoadAccidents"]
# LRCN model
LRCN_model=tf.keras.models.load_model("D:/EDI_SEM6/Intelligent_Public_surveillance_System/Model_v2_f4_A55.h5") 
#Prediction function
def predict_single_action(raw_frames, SEQUENCE_LENGTH):
    '''
    This function will perform single action recognition prediction on real time video
    Args:
    Raw_frames:  List of frames of the real time video.
    SEQUENCE_LENGTH:  The fixed number of frames of a video that can be passed to the model as one sequence.
    '''

    frames_list = []
    predicted_class_name = ''
    for frame_counter in range(SEQUENCE_LENGTH):
        frame=raw_frames[frame_counter]
        resized_frame = cv2.resize(frame, (IMAGE_HEIGHT, IMAGE_WIDTH))
        normalized_frame = resized_frame / 255
        frames_list.append(normalized_frame)
    predicted_labels_probabilities = LRCN_model.predict(np.expand_dims(frames_list, axis = 0))[0]
    print(predicted_labels_probabilities)
    predicted_label = np.argmax(predicted_labels_probabilities)
    predicted_class_name = CLASSES_LIST[predicted_label]
    print(f'Action Predicted: {predicted_class_name}\nConfidence: {predicted_labels_probabilities[predicted_label]}')
    return predicted_label,predicted_labels_probabilities[predicted_label]


#YOLO
yolo=cv2.dnn.readNet("./yolov3.weights","./yolov3.cfg")
classes=[]
with open("./coco.names",'r') as f:
    classes=f.read().splitlines()
#globals 
user_data={}



def show_registration_page():
    hide_all_frames()
    registration_frame.pack(fill="both", expand=True)

def show_login_page():
    hide_all_frames()
    login_frame.pack(fill="both", expand=True)

def show_home_page():
    hide_all_frames()
    home_frame.pack(fill="both", expand=True)

def show_analytics_page():
    hide_all_frames()
    analytics_frame.pack(fill="both", expand=True)

def hide_all_frames():
    for frame in (registration_frame, login_frame, home_frame, analytics_frame):
        frame.pack_forget()

def register_user():
    name = name_entry.get()
    username = username_entry.get()
    password = password_entry.get()
    # Here you would add code to save the user info (e.g., in a database or file)
    messagebox.showinfo("Registration", "User registered successfully!")
    show_login_page()

def login_user():
    username = login_username_entry.get()
    password = login_password_entry.get()
    # Here you would add code to verify the user info (e.g., check against a database or file)
    messagebox.showinfo("Login", "Login successful!")
    show_home_page()
def play_video(video):
    fs = gridfs.GridFS(db)
    # print(video)
    counter=0
    while True:
        frame_data = fs.get( ObjectId(video['frame_ids'][counter])).read()
        frame = np.frombuffer(frame_data, dtype=np.uint8)
        frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
        cv2.imshow('video', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        counter+=1
        if(counter==len(video['frame_ids'])):
            counter=0
    cv2.destroyAllWindows()


 
  

def load_videos():
    response=requests.post("http://127.0.0.1:5000/api/getVideos")
    data=response.json()['res']
    numVideos=len(data)
    surveillance_frame.columnconfigure((0),weight=1)
    temp=(0,1)
    if(numVideos):
        temp=tuple([x for x in range(numVideos)])
    surveillance_frame.rowconfigure(temp,weight=1)
    print("reloaded!!")
    
    for i in range(numVideos):
        video=tk.Frame(surveillance_frame,highlightbackground='black',highlightthickness=2)
        video.grid(row=i,column=0,sticky='nsew',padx=5,pady=5)
        video.columnconfigure((0,1,2,3),weight=1)
        video.rowconfigure(0,weight=1)
        video_label=tk.Label(video,text=data[i]['name'],bg='white',padx=5,pady=5)
        video_btn=tk.Button(video,text="Play",command=lambda vid=data[i]:threading.Thread(target=play_video(vid)).start())
        video_analytics=tk.Button(video,text="Analytics",command=show_analytics_page)
        video_label.grid(row=0,column=0,sticky='ew')
        video_btn.grid(row=0,column=2,sticky='ew')
        video_analytics.grid(row=0,column=3,sticky='ew')

def start_video():
    video=cv2.VideoCapture(0)
    frames=[]
    video_data={"date":"","name":"","frame_ids":[],"density":[]}
    # anomaly_data={"date":"","time":"","frame_ids":[] }
    anomaly_videos=[]
    fs = gridfs.GridFS(db)
    raw_frames=[]
    cnt=0
    num_person=0
    while True:  
        ok,frame=video.read()

        if not ok:
            break
        raw_frames.append(frame)
        # Anomaly Detection
        if len(raw_frames)==20:
            predicted_label,probability=predict_single_action(raw_frames,SEQUENCE_LENGTH)
            if(probability>=0.5):
                anomaly_videos.append({"raw_frames":raw_frames,"predicted_label":int(predicted_label),"confidence":probability})
            raw_frames.clear()
        #Person Density Calculation

        # frame = cv2.resize(frame, (frame_width, frame_height))
        height, width, _ = frame.shape
        if(cnt%100==0):
            now = datetime.now()
            current_time = now.strftime("%H%M")
            num_person=0
            blob = cv2.dnn.blobFromImage(frame, 1/255, (320, 320), (0, 0, 0), swapRB=True, crop=False)
            yolo.setInput(blob)
            output_layer_name = yolo.getUnconnectedOutLayersNames()
            layeroutput = yolo.forward(output_layer_name)
            boxes = []
            confidences = []
            class_ids = []

            for output in layeroutput:
                for detection in output:
                    scores = detection[5:]
                    class_id = np.argmax(scores)
                    confidence = scores[class_id]
                    if confidence > 0.7:
                        center_x = int(detection[0] * width)
                        center_y = int(detection[1] * height)
                        w = int(detection[2] * width)
                        h = int(detection[3] * height)
                        x = int(center_x - w / 2)
                        y = int(center_y - h / 2)
                        boxes.append([x, y, w, h])
                        confidences.append(float(confidence))
                        class_ids.append(class_id)

            indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)
            font = cv2.FONT_HERSHEY_PLAIN
            colors = np.random.uniform(0, 255, size=(len(boxes), 3))
            
            if(len(indexes)>0):
                for i in indexes.flatten():
                    x, y, w, h = boxes[i]
                    label = str(classes[class_ids[i]])
                    if(class_ids[i]==0):
                        num_person+=1
                    confi = str(round(confidences[i], 2))
                    color = colors[i]
                    # cv2.rectangle(frame, (x, y), (x+w, y+h), color, 1)
                    # cv2.putText(frame, label + " " + confi, (x, y+20), font, 2, (0, 0, 255), 1)
            video_data['density'].append([current_time,num_person])
        cv2.putText(frame, "Persons:" + " " + str(num_person), (40, 20), font, 2, (0, 0, 255), 2)
        cv2.imshow('video',frame)
        cnt+=1
        # print(cnt)
        # Store frame in GridFS
        _,buffer=cv2.imencode('.jpg', frame)
        frame_id = fs.put(buffer.tobytes())
        frames.append(frame_id)


        if cv2.waitKey(1) & 0xFF==ord('q'):
            break




    video.release()
    cv2.destroyAllWindows()
  

    video_data["date"]=str(datetime.now()).split()[0]
    video_data["name"]="surveillance_"+str(datetime.now())
    video_data["frame_ids"]=frames
    #anomaly videos added to the database
    anomaly_body=[]
    for x in anomaly_videos:
        anomaly_frames=[]
        for y in x['raw_frames']:
            _,buffer=cv2.imencode('.jpg', y)
            frame_id = fs.put(buffer.tobytes())
            anomaly_frames.append(frame_id)
        anomaly_body.append({"date":str(datetime.now()).split()[0],"time":str(datetime.now()).split()[1],"frame_ids":anomaly_frames,"predicted_label":x['predicted_label'],"confidence":x["confidence"]})


    if len(anomaly_body):
         response_anomaly=requests.post("http://127.0.0.1:5000/api/addAnomaly",data=json.dumps(anomaly_body,default=str))
    response_video=requests.post("http://127.0.0.1:5000/api/addVideo",data=json.dumps(video_data,default=str))
    load_videos()


def load_profile():
    profile_frame.columnconfigure((0,1,2,3),weight=1)
    profile_frame.rowconfigure((0),weight=1)
    start_surveillance=tk.Button(profile_frame,text="start",command=lambda: threading.Thread(target=start_video).start())
    start_surveillance.grid(row=0,column=3,sticky='ew',padx=5,pady=5)


# Main application window
app = tk.Tk()
app.title("Multi-Page GUI")
app.geometry("800x500")

# Registration page
registration_frame = tk.Frame(app)
registration_frame.grid_columnconfigure(0, weight=1)
registration_frame.grid_columnconfigure(2, weight=1)
registration_frame.grid_rowconfigure(0, weight=1)
registration_frame.grid_rowconfigure(5, weight=1)

tk.Label(registration_frame, text="Registration Page").grid(row=1, column=1, pady=10)
tk.Label(registration_frame, text="Name").grid(row=2, column=0, sticky='e')
tk.Label(registration_frame, text="Username").grid(row=3, column=0, sticky='e')
tk.Label(registration_frame, text="Password").grid(row=4, column=0, sticky='e')

name_entry = tk.Entry(registration_frame)
username_entry = tk.Entry(registration_frame)
password_entry = tk.Entry(registration_frame, show="*")

name_entry.grid(row=2, column=1)
username_entry.grid(row=3, column=1)
password_entry.grid(row=4, column=1)

tk.Button(registration_frame, text="Register", command=register_user).grid(row=5, column=0, pady=10)
tk.Button(registration_frame, text="Already have an account", command=show_login_page).grid(row=5, column=1)

# Login page
login_frame = tk.Frame(app)
login_frame.grid_columnconfigure(0, weight=1)
login_frame.grid_columnconfigure(2, weight=1)
login_frame.grid_rowconfigure(0, weight=1)
login_frame.grid_rowconfigure(4, weight=1)

tk.Label(login_frame, text="Login Page").grid(row=1, column=1, pady=10)
tk.Label(login_frame, text="Username").grid(row=2, column=0, sticky='e')
tk.Label(login_frame, text="Password").grid(row=3, column=0, sticky='e')

login_username_entry = tk.Entry(login_frame)
login_password_entry = tk.Entry(login_frame, show="*")

login_username_entry.grid(row=2, column=1)
login_password_entry.grid(row=3, column=1)

tk.Button(login_frame, text="Login", command=login_user).grid(row=4, column=0, pady=10)
tk.Button(login_frame, text="Don't have an account", command=show_registration_page).grid(row=4, column=1)

# Home page
home_frame = tk.Frame(app,bg='red')
home_frame.columnconfigure(0,weight=1)
home_frame.rowconfigure((0,1),weight=1)
profile_frame=tk.Frame(home_frame,bg='red')
surveillance_frame=tk.Frame(home_frame,bg='purple')

profile_frame.grid(row=0,column=0,sticky='nsew')
surveillance_frame.grid(row=1,column=0,sticky='nsew')
load_profile()
load_videos()




# # tk.Label(home_frame, text="Home Page").pack(pady=10)
# tk.Button(home_frame, text="Analytics", command=show_analytics_page).grid(row=0,column=0,sticky='nsew')
# # tk.Button(home_frame, text="Logout", command=show_login_page).pack(pady=5)
# tk.Button(home_frame,text="Open Video",command=lambda:threading.Thread(target=start_video).start()).grid(row=1,column=0,sticky='nsew')








# Analytics page
analytics_frame = tk.Frame(app)
tk.Label(analytics_frame, text="Analytics Page").pack(pady=10)
tk.Button(analytics_frame, text="Back", command=show_home_page).pack()

# Start with the registration page
show_registration_page()
# show_home_page()
app.mainloop()
