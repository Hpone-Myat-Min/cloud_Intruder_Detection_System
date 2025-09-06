import os
import boto3
from picamera2 import Picamera2, Preview
from datetime import datetime
import time
import requests
from rgbmatrix5x5 import RGBMatrix5x5
import serial
import threading
from queue import Queue

EC2_API_URL = "http://56.228.35.90:5000/detect" # Server endpoint
s3 = boto3.client('s3') 
is_monitoring =  False
image_queue = Queue()

def upload_to_cloud(file_paths, bucket_name):
    # Uploading captured images to S3 bucket
    filenames = []

    for file_path in file_paths:
        s3_key = os.path.basename(file_path)
        try:
            s3.upload_file(file_path, bucket_name,s3_key)
            filenames.append(s3_key)

        except FileNotFoundError:
            print("File not found")
        except NoCredentialsError:
            print("Credentials not found")
    
    image_queue.put(filenames) # Put the images into queue to trigger the cloud 

def trigger_cloud():
    # Trigger Cloud by sending POST request to its endpoint
    while True:
        images = image_queue.get()
        if images:
            try:
                response = requests.post(EC2_API_URL, json={"images":images})
                result = response.json()
                print(f"{result}")

                if result["results"] == "INTRUDER":
                    trigger_alert()

            except Exception as e:
                print("Failed",e)
        image_queue.task_done()

def trigger_alert():
    # Switch on the Red LED if intruder is detected
    print("INTRUDERRRRRRR !!!!")
    # rgbmatrix = RGBMatrix5x5()
    # rgbmatrix.set_all(255, 0, 0)
    # rgbmatrix.show()

    # time.sleep(10)
    # rgbmatrix.clear()
    # rgbmatrix.show()

def start_monitoring():
    # Capture 10 photos with 1 second interval 
    global is_monitoring
    is_monitoring = True
    picam = Picamera2()
    picam.start_preview(Preview.QT)
    picam.start()

    print("I AM CAPTURING\n")
    image_paths = []

    capture_start_time = time.time()                                     # overall start time of image capturing

    for i in range(10):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = "image_" + timestamp + "_" + str(i)
        image_location = f"/home/pi/cloud_Intruder_Detection_System/Images/{filename}.jpg"
        image_paths.append(image_location)
        print(f"Image {i} is captured")
        time.sleep(1)
    print("all images sent to cloud")
    capture_end_time = time.time()                                      # overall end time of image capturing
    picam.stop_preview()
    picam.close()

    threading.Thread(target=upload_to_cloud(image_paths,"intruder-detection-images")).start()

    serial_port.reset_input_buffer()
    is_monitoring = False

if __name__ == "__main__":
    threading.Thread(target=trigger_cloud, daemon=True).start()
    serial_port = serial.Serial('/dev/rfcomm0', baudrate=9600, timeout=1)

    print("Starting to listen")

    while True:
        motion_status = serial_port.readline().decode('utf-8').strip() # listening for bluetooth serial signal
        if motion_status == "MOTION_DETECTED" and not is_monitoring:
            print("PIR detects motion and now camera will be open")
            start_monitoring()