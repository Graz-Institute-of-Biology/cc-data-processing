
import numpy as np
import os
from PIL import Image
import cv2

def remove_background(img, mask):
    mask_ = mask.copy()
    mask_[mask_ > 0] = 1
    mask_ = np.expand_dims(mask_, axis=2)
    img = img*mask_

    return img


# file_dir = "C:\\Users\\faulhamm\\Documents\\Philipp\\Code\\cc-machine-learning\\results\\train_tf_bg_removed"
file_dir = "C:\\Users\\faulhamm\\Documents\\Philipp\\Code\\cc-machine-learning\\results\\train_tf_bg_removed\\bg_removal"


for file in os.listdir(file_dir):
    if file.endswith(".JPG"):
        img_path = os.path.join(file_dir, file)
        mask_path = img_path.replace(".JPG", "_mask.png")
        img_data = cv2.cvtColor(cv2.imread(img_path), cv2.COLOR_BGR2RGB)
        mask_data = np.array(Image.open(mask_path))

        img_no_bg = remove_background(img_data, mask_data)
        img_no_bg_ = Image.fromarray(img_no_bg)
        img_no_bg_.save(img_path.replace(".JPG", "_no_bg.JPG"))