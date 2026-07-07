
import numpy as np
import os
from PIL import Image
import cv2
from tqdm import tqdm

def remove_background(img, mask):
    mask_ = mask.copy()
    mask_[mask_ > 0] = 1
    mask_ = np.expand_dims(mask_, axis=2)
    img = img*mask_

    return img

def load_data(img_path, mask_path):

    try:
        img_data = cv2.cvtColor(cv2.imread(img_path), cv2.COLOR_BGR2RGB)
    except:
        print("Error loading image: ", img_path)
        return None, None
    
    try:
        mask_data = np.array(Image.open(mask_path))
    except:
        print("Error loading mask: ", mask_path)
        return None, None

    return img_data, mask_data

# file_dir = "C:\\Users\\faulhamm\\Documents\\Philipp\\Code\\cc-machine-learning\\results\\train_tf_bg_removed"
# file_dir = "C:\\Users\\faulhamm\\Documents\\Philipp\\Code\\cc-machine-learning\\results\\train_tf_bg_removed\\bg_removal"
# file_dir = "/usr/people/EDVZ/faulhamm/cc-machine-learning/test_tf"

file_dir = "/usr/people/EDVZ/faulhamm/cc-machine-learning/test_c"


for file in tqdm(os.listdir(file_dir)):
    if file.endswith(".JPG"):
        img_path = os.path.join(file_dir, file)
        mask_path = img_path.replace(".JPG", "_mask.png")

        img_data, mask_data = load_data(img_path, mask_path)

        if img_data is None or mask_data is None:
            continue

        img_no_bg = remove_background(img_data, mask_data)
        img_no_bg_ = Image.fromarray(img_no_bg)
        img_no_bg_.save(img_path.replace(".JPG", "_no_bg.JPG"))