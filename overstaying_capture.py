import cv2
import datetime
import os

def capture_overstaying_vehicle(image, plate_number, folder="overstaying_capture"):
    # 确保目标文件夹存在
    if not os.path.exists(folder):
        os.makedirs(folder)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{folder}/overstaying_{plate_number}_{timestamp}.jpg"
    cv2.imwrite(filename, image)
    return filename