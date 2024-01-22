import time
import cv2
import imutils
import sys
import os

sys.path.insert(1, "../src/e3v3se_display")
from TJC3224 import TJC3224_LCD

"""
Script to automate the icon id retrieval of the 
creality E3V3SE display by brute-forcing the 
draw_icon with all possible lib and icon ids.
Images are saved into a folder "icon_database_..."
with following name "<LIBID>_<ICONID>.jpg>.
"""

save_folder = "icon_database_fw_1_0_6"
com_port = "COM3"
baud_rate = 115200
screen_width = 240
screen_height = 320
delay_between_loops_in_s = (
    0.1  # A better webcam connected via usb can have a shorter delay
)

screen = TJC3224_LCD(com_port, baud_rate)
cam = cv2.VideoCapture(0)

if not cam.isOpened():
    print("Error: Could not open webcam.")
    raise Exception("Error: Could not open webcam.")

images_saved = 0

# Create a save directory if it does not exist
if not os.path.exists(save_folder):
    os.makedirs(save_folder)

for lib_id in range(0, 65):
    for icon_id in range(255):
        screen.clear_screen(screen.color_white)
        screen.draw_icon(lib_id, icon_id, screen_width // 5, screen_height // 4)
        # Give some time to make sure the camera feed sees the icon (as my wifi camera has a delay)
        time.sleep(delay_between_loops_in_s)
        # Capture frame from camera
        ret, frame = cam.read()
        if not ret:
            print("Error: Could not capture frame.")
            raise Exception("Error: Could not capture frame.")

        # Resize the frame to save space
        frame = imutils.resize(frame, width=200)
        image_name = str(lib_id) + "_" + str(icon_id) + ".jpg"
        image_path = os.path.join(save_folder, image_name)
        # Save the image
        cv2.imwrite(image_path, frame)

        print(f"Saving {image_name}")
        images_saved += 1

# Release the webcam
cam.release()
print(f"Finish! {images_saved} images were saved in folder {save_folder}")
