import os
import boto3
from picamera2 import Picamera2, Preview
from datetime import datetime
import time
import requests
from rgbmatrix5x5 import RGBMatrix5x5
import serial

EC2_API_URL = "http://56.228.35.90:5000/detect"
s3 = boto3.client('s3')
is_monitoring =  False

def upload_to_cloud(file_path, bucket_name, s3_key=None):
    if s3_key is None:
        s3_key = os.path.basename(file_path)

    try:
        s3.upload_file(file_path, bucket_name,s3_key)
        # print(f"Image Uploaded to s3 cloud {bucket_name}")
        return True

    except FileNotFoundError:
        print("File not found")
    except NoCredentialsError:
        print("Credentials not found")

    return False

def trigger_cloud(s3_keys):
    try:
        response = requests.post(EC2_API_URL, json={"images":s3_keys})
        result = response.json()
        print(f"{result}")

        if result["results"] == "INTRUDER":
            trigger_alert()

    except Exception as e:
        print("Failed",e)

def trigger_alert():
    rgbmatrix = RGBMatrix5x5()
    rgbmatrix.set_all(255, 0, 0)
    rgbmatrix.show()

    time.sleep(10)
    rgbmatrix.clear()
    rgbmatrix.show()

def start_monitoring():
    global is_monitoring
    is_monitoring = True
    picam = Picamera2()
    picam.start_preview(Preview.QT)
    picam.start()

    print("I AM CAPTURING")
    print("\n")
    image_paths = []
    s3_keys = []

    capture_start_time = time.time()                                     # overall start time of image capturing

    for i in range(10):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = "image_" + timestamp + "_" + str(i)
        image_location = f"/home/pi/cloud_Intruder_Detection_System/Images/{filename}.jpg"
        image_paths.append(image_location)
        picam.capture_file(image_location)
        key = upload_to_cloud(image_location, "intruder-detection-images")

        if key:
            s3_keys.append(f"{filename}.jpg")

        # print(f"Image {i} is captured")
        time.sleep(1)
    print("all images sent to cloud")
    capture_end_time = time.time()                                      # overall end time of image capturing
    picam.stop_preview()
    picam.close()

    if s3_keys:
        trigger_cloud(s3_keys)

    is_monitoring = False

if __name__ == "__main__":
    serial_port = serial.Serial('/dev/rfcomm0', baudrate=9600, timeout=1)

    print("Starting bluetooth")

    while True:
        motion_status = serial_port.readline().decode('utf-8').strip()
        if motion_status == "MOTION_DETECTED" and not is_monitoring:
            print("PIR detects motion and now camera will be open")
            start_monitoring()