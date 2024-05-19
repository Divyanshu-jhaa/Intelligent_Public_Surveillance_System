import tkinter as tk
from tkinter import messagebox
import threading
import numpy as np
import json
import cv2
import requests
import base64
import datetime
from bson.objectid import ObjectId
import time
import gridfs
from pymongo import MongoClient
#globals 

video_data=[]
anomaly_data=[]
user_data={}
#db connection
client=MongoClient("mongodb://localhost:27017")
db=client.SurveillanceDB
user_records=db.user_records
video_records=db.video_records
anomaly_records=db.anomaly_records


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
        video_analytics=tk.Button(video,text="Analytics")
        video_label.grid(row=0,column=0,sticky='ew')
        video_btn.grid(row=0,column=2,sticky='ew')
        video_analytics.grid(row=0,column=3,sticky='ew')

def start_video():
    video=cv2.VideoCapture(0)
    frames=[]
    video_data={"date":"","name":"","frame_ids":[]}
    fs = gridfs.GridFS(db)

    while True:
        ok,frame=video.read()
        cv2.imshow('video',frame)
        _,buffer=cv2.imencode('.jpg', frame)
        # Store frame in GridFS
        frame_id = fs.put(buffer.tobytes())
        frames.append(frame_id)
        # time.sleep(1)
      
        if cv2.waitKey(1) & 0xFF==ord('q'):
            break
    video.release()
    cv2.destroyAllWindows()
  

    video_data["date"]="19.05.24"
    video_data["name"]="surveillance_"+str(datetime.datetime.now())
    video_data["frame_ids"]=frames

    response=requests.post("http://127.0.0.1:5000/api/addVideo",data=json.dumps(video_data,default=str))
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
# show_registration_page()
show_home_page()
app.mainloop()
