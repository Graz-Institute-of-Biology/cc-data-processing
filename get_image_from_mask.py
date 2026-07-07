import os
import shutil


img_folder = r"C:\Users\faulhamm\Documents\Philipp\training\datasets\ATTO\v16_increased_candidates"
mask_folder = r"C:\Users\faulhamm\Documents\Philipp\training\datasets\ATTO\dataset_v16_0_mixed_increased\combined_masks"

for img in os.listdir(mask_folder):
    if img.endswith('.png'):
        img_name = img.replace('.png', '.JPG')
        img_path = os.path.join(img_folder, img_name)
        if os.path.exists(img_path):
            shutil.copy(img_path, r"C:\Users\faulhamm\Documents\Philipp\training\datasets\ATTO\dataset_v16_0_mixed_increased\imgs")
        # print(img_name)