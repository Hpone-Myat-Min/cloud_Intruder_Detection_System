import os
import boto3
from picamera2 import Picamera2, Preview
from datetime import datetime
import time



s3 = boto3.client('s3')

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
        image_location = f"/home/pi/object_detection/Images/{filename}.jpg"
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

    print(s3_keys)

    if s3_keys:
        trigger_cloud(s3_keys)


    # image_queue.append(image_paths)
    is_monitoring = False