import cv2
import numpy as np
import matplotlib.pyplot as plt
import time
yolo=cv2.dnn.readNet("./yolov3.weights","./yolov3.cfg")
classes=[]
with open("./coco.names",'r') as f:
    classes=f.read().splitlines()
# video = cv2.VideoCapture("http://192.0.0.4:8080/video")
video = cv2.VideoCapture(0)

frame_width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
frame_rate = int(video.get(cv2.CAP_PROP_FPS))

frame_width = 600
frame_height = 400

skip_frames = 5
num_person=0
cnt=0
while True:
    # for _ in range(skip_frames):
        
    #     ret, _ = video.read()

    ret, frame = video.read()

    if not ret:
        break

    frame = cv2.resize(frame, (frame_width, frame_height))
    height, width, _ = frame.shape
    if(cnt%100==0):
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
    


    cv2.putText(frame, "Persons" + " " + str(num_person), (20, 20), font, 2, (0, 0, 255), 2)

    cv2.imshow('video', frame)
    # time.sleep(0.05)
    cnt+=1

    if cv2.waitKey(1) & 0xFF==ord('q'):
        break

video.release()
cv2.destroyAllWindows()